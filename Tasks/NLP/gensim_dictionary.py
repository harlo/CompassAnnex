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
	wiki_bow_corpus = os.path.join(dictionary_dir, "wiki_en_bow.mm")
	wiki_dict = os.path.join(dictionary_dir, "wiki_en_wordids.txt")
	wiki_tfidf = os.path.join(dictionary_dir, "wiki_en_tfidf.mm.bz2")

	'''
	for required in [wiki_dict, wiki_bow_corpus, wiki_tfidf]:
		if not os.path.exists(required):
			print "\n\n************** %s [WARNING] ******************\n" % task_tag
			print "THIS COULD TAKE AWHILE (LIKE, 10+ HOURS)..."
			uv_task.daemonize()

			from fabric.api import settings, local
			os.chdir(dictionary_dir)
			
			gensim_dict_raw = os.path.join(dictionary_dir, "enwiki-latest-pages-articles.xml.bz2")
			
			if not os.path.exists(gensim_dict_raw):				
				with settings(warn_only=True):
					local("wget http://dumps.wikimedia.org/enwiki/latest/enwiki-latest-pages-articles.xml.bz2")


			with settings(warn_only=True):
				local("python -m gensim.scripts.make_wiki %s %s" % (
					os.path.join(dictionary_dir, "enwiki-latest-pages-articles.xml.bz2"), 
					os.path.join(dictionary_dir, "wiki_en")))

			print "WIKI CORPUS SAVED AND SERIALIZED."
			
			with settings(warn_only=True):
				local("bzip2 %s" % os.path.join(dictionary_dir, "wiki_en_tfidf.mm"))

			break

		print "Found required gensim asset %s" % required
	'''

	uv_task.finish()
	print "\n\n************** %s [END] ******************\n" % task_tag