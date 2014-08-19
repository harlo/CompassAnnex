from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def extractPDFText(task):
	task_tag = "PDF TEXT EXTRACTION"
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

	"""
		In this task, we might be asked to extract from a broken-up sub-group of documents.
		if so, that should be set in the task's properties.
		
	"""
	texts = [None] * pdf.total_pages
	
	if pdf.hasParts():
		extractors = pdf.getParts()
	else:
		extractors = [pdf.file_name]
	
	count = 0
	for e in extractors:
		if e == pdf.file_name:
			pdf_reader = pdf.loadFile(e)
		else:
			pdf_reader = pdf.loadAsset(e)
			print e

		try:
			num_pages = pdf_reader.getNumPages()
		except AttributeError as e:
			print e
			continue

		for x in xrange(0, num_pages):
			texts[count] = pdf_reader.getPage(x).extractText()
			count += 1
	
	asset_path = pdf.addAsset(texts, "doc_texts.json", as_literal=False,
		description="jsonified texts in document; page-by-page, segment-by-segment. uncleaned. (Not OCR)", tags=[ASSET_TAGS['TXT_JSON']])

	if asset_path is not None: 
		pdf.addFile(asset_path, None, sync=True)
		
		from lib.Worker.Models.uv_text import UnveillanceText
		uv_text = UnveillanceText(inflate={
			'media_id' : pdf._id,
			'searchable_text' : texts,
			'file_name' : asset_path
		})

		pdf.text_id = uv_text._id
		pdf.save()

	del texts

	pdf.addCompletedTask(task.task_path)
	task.routeNext(inflate={ 'text_file' : asset_path })
	task.finish()

	print "\n\n************** PDF TEXT EXTRACTION [END] ******************\n"