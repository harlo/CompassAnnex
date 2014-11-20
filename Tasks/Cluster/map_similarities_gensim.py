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

	import json, re, os, logging, bz2
	from gensim import corpora, models

	from lib.Worker.Models.uv_document import UnveillanceDocument
	from lib.Core.Utils.funcs import cleanLine
	from conf import DEBUG, ANNEX_DIR, getConfig
	from vars import ASSET_TAGS

	logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

	try:
		wiki_dictionary = corpora.Dictionary.load_from_text(os.path.join(
			getConfig('compass.gensim.training_data'), 'wiki_en_wordids.txt'))
		wiki_corpus = corpora.MmCorpus(bz2.BZ2File(os.path.join(
			getConfig('compass.gensim.training_data'), 'wiki_en_tfidf.mm.bz2')))
	except Exception as e:
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		error_msg = "having trouble loading gensim dictionary and corpus from wiki dump: (error type %s)" % type(e)

		print error_msg
		print e
		
		task.fail(message=error_msg)
		return

	wiki_log_entropy_file = os.path.join(getConfig('compass.gensim.training_data'), 'wiki_en_log_entropy.model')
	if not os.path.exists(wiki_log_entropy_file):
		print "\n\n************** %s [WARN] ******************\n" % task_tag
		print "no pre-prepared log entropy model.  going to generate this here, now.  might take a minute..."
		
		logent_transformation = models.LogEntropyModel(wiki_corpus, id2word=wiki_dictionary)
		logent_transformation.save(wiki_log_entropy_file)
	else:
		logent_transformation = models.LogEntropyModel.load(wiki_log_entropy_file)
		
	tokenize_function = corpora.wikicorpus.tokenize

	cluster_corpus = []
	document_map = {
		'query' : uv_task.query,
		'map' : [],
		'topics' : []
	}

	query_rx = re.compile(r'.*%s.*' % "|".join(uv_task.query))
	for doc_idx, document in enumerate([UnveillanceDocument(_id=d) for d in uv_task.documents]):

		doc_valid = True
		for required in ['_id']:
			
			if required not in document.emit().keys():				
				doc_valid = False
				break

		if not doc_valid:
			error_msg = "Document is invalid"
			print "\n\n************** %s [WARN] ******************\n" % task_tag
			uv_task.communicate(message=error_msg)
			print error_msg

			continue


		uv_task.communicate(message="Processing %s (%d out of %d)" % (
			document._id if not hasattr(document, "file_alias") else document.file_alias, doc_idx, len(uv_task.documents)))
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
			error_msg = "no document groups created"
			print error_msg
			print "\n\n************** %s [ERROR] ******************\n" % task_tag
			uv_task.fail(message=error_msg)
			return

	# make a corpus out of the concerned pages
	if len(cluster_corpus) > 0:
		uv_task.communicate(message="Building topic model...")
		cluster_corpus = logent_transformation[cluster_corpus]

		wiki_tfidf_file = os.path.join(getConfig('compass.gensim.training_data'), 'wiki_en_tfidf.tfidf_model')
		if not os.path.exists(wiki_tfidf_file):
			print "\n\n************** %s [WARN] ******************\n" % task_tag
			print "no pre-prepared tfidf model.  going to generate this here, now.  might take a minute..."
			
			wiki_tfidf = models.TfidfModel(wiki_corpus)
			wiki_tfidf.save(wiki_tfidf_file)
		else:
			wiki_tfidf = models.TfidfModel.load(wiki_tfidf_file)

		cluster_tfidf = wiki_tfidf[cluster_corpus]
		
		num_topics = 35

		lsi = models.LsiModel(corpus=cluster_tfidf, id2word=wiki_dictionary, num_topics=num_topics)
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

							break

					except Exception as e:
						continue

				if page_item_index != -1:
					break

		t_lambda = lambda x : [float(x[0]), x[1]]
		for t_group in [t.split("+") for t in [str(topic) for topic in lsi.print_topics(num_topics)]]:
			document_map['topics'].append([t_lambda(t.strip().replace('\"', '').split("*")) for t in t_group])

		if DEBUG:
			print document_map['topics']

	# save massaged data to task outupt
	if not uv_task.addAsset(document_map, "gensim_similarity_output.json", 
		as_literal=False, tags=[ASSET_TAGS['C_RES']]):
		
		error_msg = "could not save result asset to this task."
		print error_msg
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		uv_task.fail(message=error_msg)
		return

	print "\n\n************** %s [END] ******************\n" % task_tag
	uv_task.finish()