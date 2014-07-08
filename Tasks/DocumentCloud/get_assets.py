from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def getAssets(uv_task):
	task_tag = "FETCHING DOCUMENTCLOUD ASSETS"
	print "\n\n************** %s [START] ******************\n" % task_tag
	print "getting DocumentCloud assets for %s" % uv_task.doc_id
	uv_task.setStatus(412)
	
	from lib.Worker.Models.cp_documentcloud_client import CompassDocumentCloudClient
	from lib.Worker.Models.uv_document import UnveillanceDocument
	from conf import DEBUG
	
	document = UnveillanceDocument(_id=uv_task.doc_id)
	
	if document is None:
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		print "Document is None"
		return
	
	if not hasattr(document, "dc_id"):
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		print "Document has not document cloud id!"
		return
	
	if not hasattr(uv_task, "auth_string"):
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		print "DocumentCloud upload needs an auth string"
		return
		
	dc_client = CompassDocumentCloudClient(auth_string=uv_task.auth_string)	
	
	dc_manifest = dc_client.download("documents/%s.json" % document.dc_id)
	if dc_manifest is None:
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		print "No DocumentCloud manifest yet for %s." % document._id
		return
	
	document.addAsset(dc_manifest, "document_cloud_manifest.json", as_literal=False,
		description="description of document on DocumentCloud",
		tags=[ASSET_TAGS['DOC_CLOUD_MANIFEST'], ASSET_TAGS['DOC_CLOUD_DOC']])
		
	dc_entities = dc_client.download("documents/%s/entities.json" % document.dc_id)
	if dc_entities is None:
		print "\n\n************** %s [WARN] ******************\n" % task_tag
		print "No DocumentCloud entiteis yet for %s." % document._id
	else:
		entity_asset = document.addAsset(dc_entities, "document_cloud_entities.json",
			as_literal=False, description="entites pulled from DocumentCloud",
			tags=[ASSET_TAGS['DOC_CLOUD_ENTITIES'], ASSET_TAGS['DOC_CLOUD_DOC']])
		
		from lib.Worker.Models.uv_text import UnveillanceText
		
		if not hasattr(document, "text_id"):
			text = UnveillanceText(inflate={
				'file_name' : entity_asset,
				'entities' : dc_entities['entities'],
				'media_id' : document._id
			})
			
			document.text_id = text._id
			document.save()
		else:
			text = UnveillanceText(_id=document.text_id)
			text.entities = dc_entities['entities']
			text.save()
		
	document.addCompletedTask(uv_task.task_path)
	uv_task.finish()
	