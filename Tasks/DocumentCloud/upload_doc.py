from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def uploadDocument(uv_task):
	task_tag = "DOCUMENTCLOUD UPLOAD"
	print "\n\n************** %s [START] ******************\n" % task_tag
	print "uploading doc %s to DocumentCloud" % uv_task.doc_id
	uv_task.setStatus(302)
	
	from lib.Worker.Models.cp_documentcloud_client import CompassDocumentCloudClient
	from lib.Worker.Models.uv_document import UnveillanceDocument
	from conf import DEBUG
	
	document = UnveillanceDocument(_id=uv_task.doc_id)
	if document is None:
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		print "Document is None"
		uv_task.fail()
		return
	
	if not hasattr(uv_task, "auth_string"):
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		print "DocumentCloud upload needs an auth string"
		uv_task.fail()
		return
		
	dc_client = CompassDocumentCloudClient(auth_string=uv_task.auth_string)	
	upload = dc_client.upload(document)
	if DEBUG: print upload
	
	if upload is None:
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		print "DocumentCloud upload needs an auth string"
		uv_task.fail()
		return
		
	document.dc_id = upload['id']
	document.save()
	
	document.addCompletedTask(uv_task.task_path)
	uv_task.finish()
	
	print "\n\n************** %s [END] ******************\n" % task_tag
	print "Uploaded document %s" % document._id