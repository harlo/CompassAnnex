from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def mapSimilaritiesGensim(uv_task):
	task_tag = "CLUSTER: GENSIM SIMILARITIES"
	print "\n\n************** %s [START] ******************\n" % task_tag

	uv_task.setStatus(302)

	for required in ["documents", "query"]:
		if not hasattr(uv_task, required):
			print "Cluster unavailable."
			print "\n\n************** %s [ERROR] ******************\n" % task_tag
			uv_task.fail()
			return

	#uv_task.daemonize()
	import json, re, os, logging, bz2
	from gensim import corpora, models

	from lib.Worker.Models.uv_document import UnveillanceDocument
	from lib.Core.Utils.funcs import cleanLine
	from conf import DEBUG, ANNEX_DIR, getConfig
	from vars import ASSET_TAGS

	logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

	wiki_dictionary = corpora.Dictionary.load_from_text(
		os.path.join(getConfig('compass.gensim.training_data'), "wiki_en_wordids.txt"))
	wiki_corpus = corpora.MmCorpus(bz2.BZ2File(
		os.path.join(getConfig('compass.gensim.training_data'), "wiki_en_tfidf.mm.bz2")))

	logent_transformation = models.LogEntropyModel(wiki_corpus, id2word=wiki_dictionary)
	tokenize_function = corpora.wikicorpus.tokenize

	cluster_corpus = []
	document_map = {
		'query' : uv_task.query,
		'map' : []
	}


	query_rx = re.compile(r'.*%s.*' % "|".join(uv_task.query))
	for document in [UnveillanceDocument(_id=d) for d in uv_task.documents]:
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

			doc_map = {
				'_id' : document._id,
				'pages' : [{ 'index_in_parent' : i } for i in concerned_pages]
			}

			try:
				entity_map = json.loads(document.loadAsset("stanford-ner_entities.json"))['uv_page_map']
			except Exception as e:
				print "\n\n************** %s [WARN] ******************\n" % task_tag
				print e
				entity_map = None

			if entity_map is not None:
				for s in doc_map['pages']:
					try:
						s['entities'] = list(set(filter(
							lambda e: s['index_in_parent'] in e['pages'], entity_map)))

					except Exception as e: pass

			try:
				texts = json.loads(document.loadAsset("doc_texts.json"))
			except Exception as e:
				print "\n\n************** %s [WARN] ******************\n" % task_tag
				print e
				texts = None

			if texts is not None:
				# topic modeling the page
				for page in concerned_pages:
					try:
						cluster_corpus.append(wiki_dictionary.doc2bow(tokenize_function(cleanLine(texts[page]))))
					except Exception as e:
						print "\n\n************** %s [WARN] ******************\n" % task_tag
						print e
						continue

					for s in doc_map['pages']:
						try:
							if s['index_in_parent'] == page:
								s['index_in_corpus']  = len(cluster_corpus) - 1
								break

						except Exception as e: pass

			document_map['map'].append(doc_map)

		if len(document_map['map']) == 0:
			print "no document groups created"
			print "\n\n************** %s [ERROR] ******************\n" % task_tag
			uv_task.fail()
			return

	# make a corpus out of the concerned pages
	if len(cluster_corpus) > 0:
		cluster_corpus = logent_transformation[cluster_corpus]

		wiki_tfidf = models.TfidfModel(wiki_corpus)
		cluster_tfidf = wiki_tfidf[cluster_corpus]
		
		lsi = models.LsiModel(corpus=cluster_tfidf, id2word=wiki_dictionary, num_topics=len(cluster_corpus))
		cluster_lsi = lsi[cluster_tfidf]

		# for all of the cluster_lsi objects, each document (a page within a doc, actually) will be rated according to its topic set
		for i, topics in enumerate(cluster_lsi):
			page_item_index = -1

			for doc_map in document_map['map']:
				for p, page_item in enumerate(doc_map['pages']):
					try:
						if page_item['index_in_corpus'] == i:
							page_item_index = p
							page_item['topic_comprehension'] = topics
							del page_item['index_in_corpus']

							print "FOUND PAGE ITEM FOR %d at %d" % (i, p)
							break

					except Exception as e: continue

				if page_item_index != -1: break

			
		document_map['topics'] = lsi.show_topics()

	# save massaged data to task outupt
	if not uv_task.addAsset(document_map, "gensim_similarity_output.json", as_literal=False):
		print "could not save result asset to this task."
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		uv_task.fail()
		return

	print "\n\n************** %s [END] ******************\n" % task_tag
	#uv_task.save(built=True)
	uv_task.finish()