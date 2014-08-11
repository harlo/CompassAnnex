from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def generatePageMap(uv_task):
	task_tag = "PAGE MAPPER"
	print "\n\n************** %s [START] ******************\n" % task_tag
	print "MAPPING PAGES FROM TEXT DOCUMENT at %s" % uv_task.doc_id
	uv_task.setStatus(412)
	
	from lib.Worker.Models.uv_document import UnveillanceDocument

	from conf import DEBUG
	from vars import ASSET_TAGS

	doc = UnveillanceDocument(_id=uv_task.doc_id)
	if doc is None:
		print "DOC IS NONE"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		return

	import os, json
	try:
		page_path = doc.getAssetsByTagName(ASSET_TAGS['TXT_JSON'])[0]['file_name']
		pages = json.loads(doc.loadFile(os.path.join(doc.base_path, page_path)))
	except Exception as e:
		if DEBUG: print e
	
	try:
		bow_path = doc.getAssetsByTagName(ASSET_TAGS['BOW'])[0]['file_name']
		bow = json.loads(doc.loadFile(os.path.join(doc.base_path, bow_path)))
	except Exception as e:
		if DEBUG: print e
	
	if pages is None or bow is None:
		print "NO PAGES OR BAG OF WORDS"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		return
	
	# with unique words in bag that are not stopwords
	# for each page, word count of each
	from numpy import intersect1d, setdiff1d
	from conf import getConfig
	
	if hasattr(uv_task, "stopwords"):
		stopwords = uv_task.stopwords
	else:	
		stopwords = os.path.join(getConfig('nlp_server.path'), "stopwords.json")
	
	try:
		with open(stopwords, 'rb') as S:
			if hasattr(uv_task, "stopwords_lang"):
				lang = uv_task.stopwords_lang
			else:
				lang = "english"
			
			stopwords = json.loads(S.read())[lang]
				
	except Exception as e:
		print "NO STOPWORDS...\n%s" % e
		print "\n\n************** %s [WARN] ******************\n" % task_tag
	
	page_map = []
	
	print "STOPWORDS: (len %d)\nTOP:\n%s\n" % (len(stopwords), stopwords[:10])
	print "BAG OF WORDS: (len %d)\nTOP:\n%s\n" % (len(bow), bow[:10])
	
	use_words = [w for w in setdiff1d(bow, stopwords).tolist() if len(w) > 1]	
	print "SIFTING BAG OF WORDS (old len: %d, new len: %d)" % (len(bow), len(use_words))
	
	for i, p in enumerate(pages):
		page_bow = p.lower().split(" ")
		words = intersect1d(use_words, page_bow).tolist()
		if len(words) == 0: continue
		
		map = []
		for word in words:
			map.append({ 'word' : word, 'count' : page_bow.count(word) })
		
		page_map.append({ 'index' : i, 'map' : map })
	
	if len(page_map) > 0:
		print page_map
		asset_path = doc.addAsset(page_map, "page_map.json", as_literal=False,
			description="word frequencies, page-by-page", tags=[ASSET_TAGS['PAGE_MAP']])
		
		print asset_path
		
		if asset_path is None or not doc.addFile(asset_path, None, sync=True):
			print "COULD NOT SAVE ASSET."
			print "\n\n************** %s [ERROR] ******************\n" % task_tag
			return
	
	doc.addCompletedTask(uv_task.task_path)
	uv_task.routeNext()
	uv_task.finish()
	print "\n\n************** %s [END] ******************\n" % task_tag
	