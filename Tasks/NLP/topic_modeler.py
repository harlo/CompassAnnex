from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def createGensimObjects(task):
	task.daemonize()

	task_tag = "GENSIM TOPIC EXTRACTION"
	print "\n\n************** %s [START] ******************\n" % task_tag
	print "USING TEXT DOCUMENT at %s" % task.doc_id
	task.setStatus(412)

	from lib.Worker.Models.uv_document import UnveillanceDocument

	from conf import DEBUG
	from vars import ASSET_TAGS

	doc = UnveillanceDocument(_id=task.doc_id)
	if doc is None:
		print "DOC IS NONE"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		task.die()
		return

	from json import loads

	try:
		texts = loads(doc.loadAsset("doc_texts.json"))
	except Exception as e:
		print "ERROR GETTING DOC-TEXTS: %s" % e
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		task.die()
		return

	import logging, os
	from json import loads
	from gensim import corpora

	from lib.Core.Utils.funcs import cleanLine
	from conf import getConfig, ANNEX_DIR

	logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
	with open(os.path.join(getConfig('nlp_server.path'), "stopwords.json"), 'rb') as SW:
		stopwords = loads(SW.read())['english']
		print stopwords

	dictionary = corpora.Dictionary(cleanLine(page).lower().split() for page in texts)
	stop_ids = [dictionary.token2id[stopword] for stopword in stopwords
		if stopword in dictionary.token2id]

	once_ids = [tokenid for tokenid, doc_freq in dictionary.dfs.iteritems()
		if doc_freq == 1]

	dictionary.filter_tokens(stop_ids + once_ids)
	dictionary.compactify()

	if DEBUG:
		print "GENSIM DICT:"
		print dictionary

	dictionary_path = doc.addAsset(None, "%s.dict" % doc.file_name,
		description="Gensim Dictionary Object", tags=[ASSET_TAGS["GM_D"]])

	if dictionary_path is None:
		print "NOPE, NO GENSIM DICT SAVED"
		task.die()
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		return

	try:
		doc.getFile(os.path.join(ANNEX_DIR, dictionary_path))
	except Exception as e:
		print "\n\n************** %s [WARN] ******************\n" % task_tag
		print e

	dictionary.save(os.path.join(ANNEX_DIR, dictionary_path))
	doc.addFile(dictionary_path, None, sync=True)

	corpus = [dictionary.doc2bow(cleanLine(page).lower().split()) for page in texts]

	if DEBUG:
		print "GENSIM CORPUS:"
		print corpus

	corpus_path = doc.addAsset(None, "%s.mm" % doc.file_name,
		description="Gensim Corpus Object (Matrix)", tags=[ASSET_TAGS["GM_MM"]])

	if corpus_path is None:
		print "NOPE, NO GENSIM MATRIX OBJ SAVED"
		task.die()
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		return

	try:
		doc.getFile(os.path.join(ANNEX_DIR, corpus_path))
	except Exception as e:
		print "\n\n************** %s [WARN] ******************\n" % task_tag
		print e

	corpora.MmCorpus.serialize(os.path.join(ANNEX_DIR, corpus_path), corpus)
	doc.addFile(corpus_path, None, sync=True)

	from gensim import models

	tfidf = models.TfidfModel(corpus)
	corpus_tfidf = tfidf[corpus]

	num_topics = 300
	lsi = models.LsiModel(corpus_tfidf, id2word=dictionary, num_topics=num_topics)
	if DEBUG:
		print "HERE ARE GENSIM'S LSI TOPICS (num_topics=%d)" % num_topics
		print lsi.print_topics()

	lsi_path = doc.addAsset(None, "%s_model.lsi" % doc.file_name,
		description="Gensim LSI Model", tags=[ASSET_TAGS["GM_LSI"]])

	if lsi_path is not None:
		try:
			doc.getFile(os.path.join(ANNEX_DIR, lsi_path))
		except Exception as e:
			print "\n\n************** %s [WARN] ******************\n" % task_tag
			print e

		lsi.save(os.path.join(ANNEX_DIR, lsi_path))
		doc.addFile(lsi_path, None, sync=True)

	doc.addCompletedTask(task.task_path)
	task.routeNext()
	print "\n\n************** %s [END] ******************\n" % task_tag
	task.finish()