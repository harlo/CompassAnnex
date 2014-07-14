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
		print "\n\n************** PDF TEXT EXTRACTION [ERROR] ******************\n"
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
		print "\n\n************** PDF TEXT EXTRACTION [ERROR] ******************\n"
		return

	from json import loads
	lower_bound = 0
	t = pdf.getAsset("doc_texts.json")
	if t is None:
		texts = [None] * total_pages
	else:
		try:
			texts = loads(t[0])
		except TypeError as e:
			texts = [None] * total_pages
		
		if hasattr(task, "split_index") : lower_bound = task.split_index

	upper_bound = lower_bound + pdf_reader.getNumPages()
	
	for x in xrange(lower_bound, upper_bound):
		texts[x] = pdf_reader.getPage(x).extractText()
		if DEBUG: print "EXTRACTED TEXT from page %d of %d:\n%s" % (x, upper_bound, texts[x])
	
	asset_path = pdf.addAsset(texts, "doc_texts.json", as_literal=False,
		description="jsonified texts in document; page-by-page, segment-by-segment. unclean. (Not OCR)", tags=[ASSET_TAGS['TXT_JSON']])

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

	pdf.addCompletedTask(task.task_path)
	
	if not hasattr(task, "no_continue"):
		from lib.Worker.Models.uv_task import UnveillanceTask
		next_task = UnveillanceTask(inflate={
			'task_path' : 'Text.preprocess_nlp.preprocessNLP',
			'doc_id' : task.doc_id,
			'queue' : task.queue,
			'text_file' : asset_path
		})
		next_task.run()
	
	if DEBUG: print "WHERE ARE THE FUCKING S TEXTS? %d" % len(pdf.searchable_texts)
	
	task.finish()
	print "\n\n************** PDF TEXT EXTRACTION [END] ******************\n"