from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def OCRPDF(task):
	task_tag = "PDF OCR-TO-TEXT"
	print "\n\n************** %s [START] ******************\n" % task_tag
	print "OCRing text from pdf at %s" % task.doc_id
	task.setStatus(412)

	from lib.Worker.Models.cp_pdf import CompassPDF

	from conf import DEBUG
	from vars import ASSET_TAGS

	pdf = CompassPDF(_id=task.doc_id)
	if pdf is None:
		print "PDF IS NONE"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		return

	"""
		In this task, we might be asked to extract from a broken-up sub-group of documents.
		if so, that should be set in the task's properties.
		
	"""
	pdf_reader = pdf.loadFile(pdf.file_name)
	total_pages = pdf_reader.getNumPages()
	if hasattr(task, "split_file"):
		pdf_reader = pdf.loadAsset(task.split_file)		

	if pdf_reader is None:
		print "PDF READER IS NONE"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		return

	lower_bound = 0
	upper_bound = lower_bound + pdf_reader.getNumPages()
	texts = [None] * total_pages

	for x in xrange(lower_bound, upper_bound):
		# TODO: OCR the doc
		texts[x] = "TBD"
	
	asset_path = pdf.addAsset(texts, "doc_ocr.json", as_literal=False,
		description="jsonified texts in document; page-by-page.  From OCR",
		tags=[ASSET_TAGS['TXT_OCR']])
	if asset_path is not None: pdf.addFile(asset_path, None, sync=True)
	
	task.finish()
	print "\n\n************** %s [END] ******************\n" % task_tag