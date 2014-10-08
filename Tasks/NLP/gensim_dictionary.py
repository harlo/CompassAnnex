from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def buildGensimDictionary(uv_task):
	task_tag = "BUILDING GENSIM DICTIONARY!!!"
	print "\n\n************** %s [START] ******************\n" % task_tag

	uv_task.setStatus(412)

	import os
	from conf import DEBUG, getConfig

	dictionary_dir = getConfig('compass.gensim.training_data')
	wiki_bow_corpus = os.path.join(dictionary_dir, "wiki_corpus.mm")
	wiki_dict = os.path.join(dictionary_dir, "wiki_dict.dict")

	for required in [wiki_dict, wiki_bow_corpus]:
		if not os.path.exists(required):
			print "\n\n************** %s [WARNING] ******************\n" % task_tag
			print "THIS COULD TAKE AWHILE (LIKE, HOURS)..."
			uv_task.daemonize()
			
			gensim_dict_raw = os.path.join(dictionary_dir, "enwiki-latest-pages-articles.xml.bz2")
			
			if not os.path.exists(gensim_dict_raw):
				from fabric.api import settings, local
				
				os.chdir(dictionary_dir)
				with settings(warn_only=True):
					local("wget http://dumps.wikimedia.org/enwiki/latest/enwiki-latest-pages-articles.xml.bz2")

			from gensim.corpora import WikiCorpus, wikicorpus, MmCorpus
			
			print "GETTING WIKI CORPUS"
			wiki_corpus = WikiCorpus(gensim_dict_raw)

			print "SAVING WIKI CORPUS"
			wiki_corpus.dictionary.save(wiki_dict)
			
			print "SERIALIZING CORUPUS"
			MmCorpus.serialize(wiki_bow_corpus, wiki_corpus)

			print "WIKI CORPUS SAVED AND SERIALIZED."
			break

		print "Found required gensim asset %s" % required

	uv_task.finish()
	print "\n\n************** %s [END] ******************\n" % task_tag