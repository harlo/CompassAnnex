from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def extractPDFText(task):
	print "\n\n************** PDF TEXT EXTRACTION [START] ******************\n"
	print "extracting text from pdf at %s" % task.doc_id
	task.setStatus(412)

	from lib.Worker.Models.cp_pdf import CompassPDF

	from conf import DEBUG
	from vars import ASSET_TAGS

	pdf = CompassPDF(_id=task.doc_id)
	if pdf is None:
		print "PDF IS NONE"
		print "\n\n************** PDF TEXT EXTRACTION [ERROR] ******************\n"
		return

	"""
		In this task, we might be asked to extract from a broken-up sub-group of documents.
		if so, that should be set in the task's properties.
		
	"""

	task.finish()
	print "\n\n************** PDF TEXT EXTRACTION [END] ******************\n"
