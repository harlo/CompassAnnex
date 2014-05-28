from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def processPDFMetadata(task):
	task_tag = "PDF METADATA EXTRACTION"
	print "\n\n************** %s [START] ******************\n" % task_tag
	print "extracting text from pdf at %s" % task.doc_id
	task.setStatus(412)

	from lib.Worker.Models.cp_pdf import CompassPDF

	from conf import DEBUG
	from vars import ASSET_TAGS

	pdf = CompassPDF(_id=task.doc_id)
	if pdf is None:
		print "PDF IS NONE"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		return
	
	from conf import ANNEX_DIR, getConfig
	from fabric.api import *
	
	peepdf = local("peepdf %s -s %s" % (
		os.path.join(ANNEX_DIR, pdf.file_name), getConfig('compass.peepdf.batch')))
	
	if DEBUG: print peepdf
	
	# save to asset, next task: compile metadata
	md_file = pdf.addAsset(peepdf, "%s.peeped" % pdf.file_name)
	if md_file is None:
		print "METADATA COULD NOT BE ADDED"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		return
	
	from lib.Worker.Models.uv_task import UnveillanceTask
	next_task = UnveillanceTask(inflate={
		'doc_id' : pdf._id,
		'md_file' : md_file,
		'md_namespace' : "PDF",
		'task_path' : "Documents.compile_metadata.compileMetadata",
		'queue' : task.queue
	})
	next_task.run()
	task.finish()
	print "\n\n************** %s [END] ******************\n" % task_tag
