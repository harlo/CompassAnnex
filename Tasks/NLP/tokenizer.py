from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def basicTokenizer(task):
	task_tag = "NLP TOKENIZER"
	print "\n\n************** %s [START] ******************\n" % task_tag
	print "TOKENIZING TEXT DOCUMENT at %s" % task.doc_id
	task.setStatus(302)

	from lib.Worker.Models.uv_document import UnveillanceDocument

	from conf import DEBUG
	from vars import ASSET_TAGS

	doc = UnveillanceDocument(_id=task.doc_id)
	if doc is None:
		print "DOC IS NONE"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		return

	txt = None
	
	from json import loads
	if hasattr(task, "txt_file"):
		txt = loads(doc.loadFile(task.txt_file))
	else:
		import os
		try:
			txt_path = doc.getAssetsByTagName(ASSET_TAGS['TXT_JSON'])[0]['file_name']
			txt = loads(doc.loadFile(os.path.join(doc.base_path, txt_path)))
		except Exception as e:
			if DEBUG: print e
	
	if txt is None:
		print "TEXT FILE IS NONE"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		return
		
	from lib.Worker.Models.cp_nlp_server import CompassNLPServer
	nlp_server = CompassNLPServer()
	tokenized = nlp_server.sendNLPRequest({
		'method' : 'tokenize',
		'txt' : txt
	})
	
	if tokenized is None:
		print "COULD NOT TOKENIZE."
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		return
	
	if DEBUG:
		print "here is res"
		print type(tokenized)
		
	asset_path = doc.addAsset(tokenized, "core_nlp_tokenized.json", as_literal=False,
		description="tokenized output from Stanford Core NLP",
		tags=[ASSET_TAGS['TOKENS_NLP']])

	if asset_path is None or not doc.addFile(asset_path, None, sync=True): 
		print "COULD NOT SAVE ASSET."
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		return
	
	doc.addCompletedTask(task.task_path)
	task.finish()
	print "\n\n************** %s [END] ******************\n" % task_tag