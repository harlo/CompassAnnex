from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def get_documentcloud_ocr(uv_task):	
	task_tag = "PULLING OCR FROM DOCUMENTCLOUD"
	print "\n\n************** %s [START] ******************\n" % task_tag
	print "OCRing text via documentcloud from pdf at %s" % uv_task.doc_id
	uv_task.setStatus(302)

	if not hasattr(uv_task, "documentcloud_id"):
		error_msg = "DOCUMENTCLOUD ID NEEDED"
		print error_msg
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		uv_task.fail(status=412, message=error_msg)
		return

	if not hasattr(uv_task, "documentcloud_auth"):
		error_msg = "DOCUMENTCLOUD AUTH STRING NEEDED"
		print error_msg
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		uv_task.fail(status=412, message=error_msg)
		return 

	from lib.Worker.Models.cp_pdf import CompassPDF
	from conf import DEBUG

	pdf = CompassPDF(_id=uv_task.doc_id)
	if pdf is None:
		print "PDF IS NONE"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		uv_task.fail()
		return

	pdf_reader = pdf.loadFile(pdf.file_name)
	if pdf_reader is None:
		print "PDF READER IS NONE"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		uv_task.fail()
		return

	import os, requests
	
	from lib.Core.Utils.funcs import cleanLine
	from Models.uv_els_stub import UnveillanceELSStub
	from conf import ANNEX_DIR
	from vars import ASSET_TAGS

	texts = [None] * pdf.total_pages
	count = 0
	req_map = {
		'a' : uv_task.documentcloud_auth,
		's' : uv_task.documentcloud_id.split('-')[0],
		'd' : "-".join(uv_task.documentcloud_id.split('-')[1:])
	}

	for x in xrange(0, num_pages):
		req_map['x'] = x
		req = "https://%(a)s@www.documentcloud.org/documents/%(s)s/pages/%(d)s-p%(x)d.txt" % (req_map)
	
		if DEBUG:
			print "trying %s" % req

		r = requests.get(req)
		if r.status_code != 200:
			print "\n\n************** %s [WARN] ******************\n" % task_tag
			print "no text at page %d" % x
		else:
			texts[count] = r.content

		count += 1

	asset_path = pdf.addAsset(texts, "doc_texts.json", as_literal=False,
		description="jsonified texts in document, from DocumentCloud", tags=[ASSET_TAGS['TXT_JSON']])

	if asset_path is not None: 
		pdf.addFile(asset_path, None, sync=True)
		pdf.save()

	del texts

	pdf.addCompletedTask(uv_task.task_path)
	uv_task.routeNext(inflate={ 'text_file' : asset_path })
	print "\n\n************** %s [END] ******************\n" % task_tag

	uv_task.finish()