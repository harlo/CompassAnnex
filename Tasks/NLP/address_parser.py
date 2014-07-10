from __future__ import absolute_import

from addresses import parse_addresses

from vars import CELERY_STUB as celery_app

@celery_app.task
def addressParser(task):
	task_tag = "NLP ADDRESS PARSER"
	print "\n\n************** %s [START] ******************\n" % task_tag
	print "EXTRACTING ADDRESSES FROM TEXT DOCUMENT at %s" % task.doc_id
	task.setStatus(412)

	from lib.Worker.Models.uv_document import UnveillanceDocument

	from conf import DEBUG
	from vars import ASSET_TAGS

	doc = UnveillanceDocument(_id=task.doc_id)
	if doc is None:
		print "DOC IS NONE"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		return

	txt = None
	if hasattr(task, "txt_file"):
		txt = doc.loadFile(task.txt_file)
	else:
		import os
		try:
			txt_path = doc.getAssetsByTagName(ASSET_TAGS['TXT_JSON'])[0]['file_name']
			txt = doc.loadFile(os.path.join(doc.base_path, txt_path))
		except Exception as e:
			if DEBUG: print e
	
	if txt is None:
		print "TEXT FILE IS NONE"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		return
	
	addresses = parse_addresses(txt)
	
	if addresses is None:
		print "COULD NOT EXTRACT ADDRESSES."
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		return
	
	if DEBUG:
		print "here is res"
		print type(addresses)
		
	asset_path = doc.addAsset(addresses, "addresses.json", as_literal=False,
		description="addresses output from Everyblock address extractor",
		tags=[ASSET_TAGS['ADDRESSES_NLP']])

	if asset_path is None or not doc.addFile(asset_path, None, sync=True): 
		print "COULD NOT SAVE ASSET."
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		return
	
	doc.addCompletedTask(task.task_path)
	task.finish()
	print "\n\n************** %s [END] ******************\n" % task_tag
