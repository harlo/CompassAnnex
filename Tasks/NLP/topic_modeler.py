from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def createGensimObjects(task):
	#task.daemonize()

	task_tag = "GENSIM TOPIC EXTRACTION"
	print "\n\n************** %s [START] ******************\n" % task_tag
	print "USING TEXT DOCUMENT at %s" % task.doc_id
	task.setStatus(302)

	from lib.Worker.Models.uv_document import UnveillanceDocument

	from conf import DEBUG
	from vars import ASSET_TAGS

	doc = UnveillanceDocument(_id=task.doc_id)
	if doc is None:
		print "DOC IS NONE"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		task.fail()
		return

	from json import loads

	try:
		texts = loads(doc.loadAsset("doc_texts.json"))
	except Exception as e:
		print "ERROR GETTING DOC-TEXTS: %s" % e
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		task.fail()
		return

	import logging, os, bz2
	from json import loads
	from gensim import corpora

	from lib.Core.Utils.funcs import cleanLine
	from conf import getConfig, ANNEX_DIR

	logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

	try:
		wiki_dictionary = corpora.Dictionary.load_from_text(
			os.path.join(getConfig('compass.gensim.training_data'), 'wiki_en_wordids.txt'))
		wiki_corpus = corpora.MmCorpus(bz2.BZ2File(
			os.path.join(getConfig('compass.gensim.training_data'), 'wiki_en_tfidf.mm.bz2')))
	except Exception as e:
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		error_msg = "having trouble loading gensim dictionary and corpus from wiki dump: (error type %s)" % type(e)

		print error_msg
		print e
		
		task.fail(message=error_msg)
		return

	from gensim import models

	logent_transformation = models.LogEntropyModel(wiki_corpus, id2word=wiki_dictionary)
	tokenize_function = corpora.wikicorpus.tokenize

	doc_corpus = [wiki_dictionary.doc2bow(cleanLine(page).lower().split()) for page in texts]
	doc_corpus = logent_transformation[doc_corpus]

	wiki_tfidf = models.TfidfModel(wiki_corpus)
	doc_tfidf = wiki_tfidf[doc_corpus]

	num_topics = 300
	lsi = models.LsiModel(corpus=doc_tfidf, id2word=wiki_dictionary, num_topics=num_topics)
	doc_lsi = lsi[doc_tfidf]

	if DEBUG:
		print "HERE ARE GENSIM'S LSI TOPICS (num_topics=%d)" % num_topics
		print doc_lsi.print_topics()

	lsi_path = doc.addAsset(None, "%s_model.lsi" % doc.file_name,
		description="Gensim LSI Model", tags=[ASSET_TAGS["GM_LSI"]])

	if lsi_path is not None:
		try:
			doc.getFile(os.path.join(ANNEX_DIR, lsi_path))
		except Exception as e:
			print "\n\n************** %s [WARN] ******************\n" % task_tag
			print e

		doc_lsi.save(os.path.join(ANNEX_DIR, lsi_path))
		doc.addFile(lsi_path, None, sync=True)

	doc.addCompletedTask(task.task_path)
	task.routeNext()
	print "\n\n************** %s [END] ******************\n" % task_tag
	task.finish()