from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def basicTokenizer(task):
	task_tag = "NLP TOKENIZER"
	print "\n\n************** %s [START] ******************\n" % task_tag
	print "TOKENIZING TEXT DOCUMENT at %s" % task.doc_id
	task.setStatus(412)

	from lib.Worker.Models.uv_document import UnveillanceDocument

	from conf import DEBUG
	from vars import ASSET_TAGS

	doc = UnveillanceDocument(_id=task.doc_id)
	if doc is None:
		print "DOC IS NONE"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		return

	if hasattr(task, "txt_file"):
		txt = doc.loadFile(doc.file_name)
	else:
		txt = doc.loadFile(task.txt_file)
	
	if txt is None:
		print "TEXT FILE IS NONE"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		return
		
	from lib.Worker.Models.cp_nlp_server import CompassNLPServer
	nlp_server = CompassNLPServer()
	tokenized = nlp_server.sendNLPRequest({
		'method' : 'tokenize',
		'txt' : txt,
		'blocking' : True 
	})
	
	if tokenized is None:
		print "COULD NOT TOKENIZE."
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		return
	
	asset_path = doc.addAsset(tokenized, "tokenized.xml",
		description="tokenized output from Stanford Core NLP",
		tags=[ASSET_TAGS['TOKENS_NLP']])

	if asset_path is None or not doc.addFile(asset_path, None, sync=True): 
		print "COULD NOT SAVE ASSET."
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		return
	
	task.finish()
	print "\n\n************** %s [END] ******************\n" % task_tag