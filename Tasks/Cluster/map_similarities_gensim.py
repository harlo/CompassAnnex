from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def mapSimilaritiesGensim(uv_task):
	task_tag = "CLUSTER: GENSIM SIMILARITIES"
	print "\n\n************** %s [START] ******************\n" % task_tag

	for required in ["documents", "query"]:
		if not hasattr(uv_task, required):
			print "Cluster unavailable."
			print "\n\n************** %s [ERROR] ******************\n" % task_tag
			return

	import json, re, os
	from gensim import corpora, models

	from lib.Worker.Models.uv_document import UnveillanceDocument
	from conf import DEBUG, getConfig
	from vars import ASSET_TAGS

	#uv_task.daemonize()
	uv_task.setStatus(412)

	wiki_dictionary = corpora.Dictionary.load(os.path.join(getConfig('compass.gensim.training_data'), "wiki_dict.dict"))
	wiki_corpus = corpora.MmCorpus(os.path.join(getConfig('compass.gensim.training_data'), "wiki_corpus.mm"))

	logent_transformation = models.LogEntropyModel(wiki_corpus, id2word=wiki_dictionary)
	tokenize_function = wiki_corpus.tokenize
	cluster_corpus = []

	document_map = {
		'query' : uv_task.query,
		'map' : []
	}

	query_rx = re.compile(r'.*%s.*' % "|".join(uv_task.query.split(",")))
		
	for document in [UnveillanceDocument(_id=d) for d in uv_task.cluster_documents]:
		concerned_pages = []

		try:
			page_map = json.loads(document.loadAsset("page_map.json"))['uv_page_map']
		except Exception as e:
			print "\n\n************** %s [WARN] ******************\n" % task_tag
			print e
			continue

		for page in page_map:
			if len([p for p in page['map'] if re.match(query_rx, p['word'])]) > 0:
				concerned_pages.append(page['index'])

		if len(concerned_pages) > 0:
			concerned_pages = list(set(concerned_pages))

			try:
				entity_map = json.loads(document.loadAsset("stanford-ner_entities.json"))['uv_page_map']
			except Exception as e:
				print "\n\n************** %s [WARN] ******************\n" % task_tag
				print e
				entity_map = None

			doc_map = {
				'_id' : document._id,
				'pages' : [{ 'index_in_parent' : i, 'entities' : [] if entity_map is None else list(set(
				[e['entity'] for e in filter(lambda e: i in e['pages'], entity_map)])) } for i in concerned_pages]
			})

			try:
				texts = json.loads(document.loadAsset("doc_texts.json"))
			except Exception as e:
				print "\n\n************** %s [WARN] ******************\n" % task_tag
				print e
				texts = None

			if texts is not None:
				for page in concerned_pages:
					try:
						cluster_corpus.append(wiki_dictionary.doc2bow(tokenize_function(text[page])))
					except Exception as e:
						print "\n\n************** %s [WARN] ******************\n" % task_tag
						print e
						continue

					try:
						page_item = filter(lambda s: s['index_in_parent'] == page, doc_map['pages'])[0]
						doc_map['pages'][doc_map['pages'].index(page_item)].update({
							'index_in_corpus' : len(cluster_corpus) - 1
						})
					except Exception as e:
						print "\n\n************** %s [WARN] ******************\n" % task_tag
						print e
			
			document_map['map'].append(doc_map)

	if len(document_map['grouping']) == 0:
		print "no document groups created"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		#uv_task.die()
		return

	# make a corpus out of the concerned pages
	if len(cluster_corpus) > 0:
		cluster_corpus = logent_transformation[cluster_corpus]

		wiki_tfidf = models.TfidfModel(wiki_corpus)
		cluster_tfidf = wiki_tfidf[cluster_corpus]
		

		lsi = models.LsiModel(corpus=cluster_tfidf, id2word=wiki_dictionary, num_topics=len(cluster_corpus))
		cluster_lsi = lsi[corpus_tfidf]

		# for all of the cluster_lsi objects, each document (a page within a doc, actually) will be rated according to its topic set
		for i, topics in enumerate(cluster_lsi):
			try:
				page_item = filter(lambda s: s['index_in_corpus'] == i, doc_map['pages'])[0]
				page_item_index = doc_map['pages'].index(page_item)

				page_item['topic_comprehension'] = topics
				del page_item['index_in_corpus']
				
				doc_map['pages'][page_item_index] = page_item
			except Exception as e:
				print "\n\n************** %s [WARN] ******************\n" % task_tag
				print e
				continue
		
		doc_map['topics'] = lsi.show_topics()

	if DEBUG:
		print "\n\n************** %s [OUTPUT!] ******************\n" % task_tag
		print doc_map
		print "\n\n"

	# save massaged data to task outupt
	if not uv_task.addAsset(doc_map, "gensim_similarity_output.json", as_literal=False):
		print "could not save result asset to this task."
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		#uv_task.die()
		return

	print "\n\n************** %s [END] ******************\n" % task_tag
	uv_task.save(built=True)