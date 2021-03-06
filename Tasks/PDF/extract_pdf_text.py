from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def extractPDFText(uv_task):	
	task_tag = "PDF TEXT EXTRACTION"
	print "\n\n************** %s [START] ******************\n" % task_tag
	print "extracting text from pdf at %s" % uv_task.doc_id
	uv_task.setStatus(302)

	from lib.Worker.Models.cp_pdf import CompassPDF

	pdf = CompassPDF(_id=uv_task.doc_id)
	if pdf is None:
		print "PDF IS NONE"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		uv_task.fail()
		return

	"""
		In this task, we might be asked to extract from a broken-up sub-group of documents.
		if so, that should be set in the task's properties.
		
	"""
	import os
	from fabric.api import settings, local
	from wand.image import Image
	from time import sleep

	from lib.Core.Utils.funcs import cleanLine, generateMD5Hash
	from Models.uv_els_stub import UnveillanceELSStub
	from conf import ANNEX_DIR, DEBUG
	from vars import ASSET_TAGS

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
		try:
			num_pages = pdf_reader.getNumPages()
		except AttributeError as e:
			print e
			continue

		for x in xrange(0, num_pages):
			text = cleanLine(pdf_reader.getPage(x).extractText())
			texts[count] = text

			els_stub = UnveillanceELSStub('cp_page_text', inflate={
				'media_id' : pdf._id,
				'searchable_text' : text,
				'index_in_parent' : count,
				'_id' : generateMD5Hash(content=pdf._id, salt=str(count))
			})

			count += 1
	
	asset_path = pdf.addAsset(texts, "doc_texts.json", as_literal=False,
		description="jsonified texts in document; page-by-page, segment-by-segment. unclean.", tags=[ASSET_TAGS['TXT_JSON']])

	if asset_path is not None: 
		pdf.addFile(asset_path, None, sync=True)
		pdf.save()

	del texts

	pdf.addCompletedTask(uv_task.task_path)
	uv_task.routeNext(inflate={ 'text_file' : asset_path })
	print "\n\n************** %s [END] ******************\n" % task_tag

	uv_task.finish()
