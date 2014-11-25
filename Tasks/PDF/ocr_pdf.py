from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def OCRPDF(uv_task):	
	task_tag = "PDF OCR-TO-TEXT"
	print "\n\n************** %s [START] ******************\n" % task_tag
	print "OCRing text from pdf at %s" % uv_task.doc_id
	task.setStatus(302)

	from lib.Worker.Models.cp_pdf import CompassPDF
	from conf import DEBUG

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
	pdf_reader = pdf.loadFile(pdf.file_name)
	if pdf_reader is None:
		print "PDF READER IS NONE"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		uv_task.fail()
		return

	import os
	from fabric.api import settings, local
	from wand.image import Image
	from time import sleep

	from lib.Core.Utils.funcs import cleanLine
	from Models.uv_els_stub import UnveillanceELSStub
	from conf import ANNEX_DIR
	from vars import ASSET_TAGS

	texts = [None] * pdf.total_pages
	count = 0
	tmp_img = os.path.join(ANNEX_DIR, pdf.base_path, "p_image.jpg")

	for x in xrange(0, num_pages):
		# pdf page to image
		with Image(filename=os.path.join(ANNEX_DIR, pdf.base_path, "%s[%d]" % (pdf.file_name, x))) as p_image:
			p_image.save(tmp_img)
			
			# image to ocr
			with settings(warn_only=True):
				text = cleanLine(local("tesseract p_image.jpg -", capture=True))
				texts[count] = text

				els_stub = UnveillanceELSStub('cp_page_text', inflate={
					'media_id' : pdf._id,
					'searchable_text' : text,
					'index_in_parent' : count
				})

			sleep(1)

		count += 1

	os.remove(tmp_img)

	asset_path = pdf.addAsset(texts, "doc_texts.json", as_literal=False,
		description="jsonified texts in document; page-by-page, segment-by-segment. unclean. (OCR'd using tesseract)",
		tags=[ASSET_TAGS['TXT_JSON']])

	if asset_path is not None: 
		pdf.addFile(asset_path, None, sync=True)
		pdf.save()

	del texts

	pdf.addCompletedTask(uv_task.task_path)
	uv_task.routeNext(inflate={ 'text_file' : asset_path })
	print "\n\n************** %s [END] ******************\n" % task_tag

	uv_task.finish()