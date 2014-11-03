from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def processPDFMetadata(uv_task):
	uv_task.daemonize()

	task_tag = "PDF METADATA EXTRACTION"
	print "\n\n************** %s [START] ******************\n" % task_tag
	print "extracting text from pdf at %s" % uv_task.doc_id
	uv_task.setStatus(302)
		
	from lib.Worker.Models.cp_pdf import CompassPDF

	from conf import DEBUG
	from vars import ASSET_TAGS

	pdf = CompassPDF(_id=uv_task.doc_id)
	if pdf is None:
		print "PDF IS NONE"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		uv_task.fail()
		return

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
		uv_task.fail()
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
		uv_task.fail()
		return
	
	pdf.addCompletedTask(uv_task.task_path)
	uv_task.routeNext(inflate={
		'md_file' : "%s.peeped" % pdf.file_name,
		'md_namespace' : "PDF"
	})
	
	print "\n\n************** %s [END] ******************\n" % task_tag
	uv_task.finish()
