from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def processPDFMetadata(uv_task):
	task_tag = "PDF METADATA EXTRACTION"
	print "\n\n************** %s [START] ******************\n" % task_tag
	print "extracting text from pdf at %s" % uv_task.doc_id
	uv_task.setStatus(412)
		
	from lib.Worker.Models.cp_pdf import CompassPDF

	from conf import DEBUG
	from vars import ASSET_TAGS

	pdf = CompassPDF(_id=uv_task.doc_id)
	if pdf is None:
		print "PDF IS NONE"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		return
	
	if DEBUG: print uv_task.emit()
	
	import os
	from conf import ANNEX_DIR, getConfig
	from fabric.api import local, settings
	
	with settings(warn_only=True):
		peepdf_raw = local("%s %s -s %s" % (
			getConfig('compass.peepdf.root'), os.path.join(ANNEX_DIR, pdf.file_name),
			getConfig('compass.peepdf.batch')), capture=True)
			
	if peepdf_raw is None:
		print "METADATA COULD NOT BE GENERATED"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		return
	
	import re
	peepdf = []
	for line in peepdf_raw.splitlines():
		if line != "":
			peepdf.append(re.compile("\033\[[0-9;]+m").sub("", line))
	
	# save to asset, next task: compile metadata
	md_file = pdf.addAsset("\n".join(peepdf), "%s.peeped" % pdf.file_name)
	if md_file is None or not pdf.addFile(md_file, None, sync=True):
		print "METADATA COULD NOT BE ADDED"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		return
	
	from lib.Worker.Models.uv_task import UnveillanceTask
	next_task = UnveillanceTask(inflate={
		'doc_id' : pdf._id,
		'md_file' : "%s.peeped" % pdf.file_name,
		'md_namespace' : "PDF",
		'task_path' : "Documents.compile_metadata.compileMetadata",
		'queue' : uv_task.queue,
		'next_task_path' : "PDF.extract_pdf_text.extractPDFText"
	})
	next_task.run()
	uv_task.finish()
	print "\n\n************** %s [END] ******************\n" % task_tag
