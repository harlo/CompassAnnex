from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def splitPDFPages(task):
	print "\n\n************** SPLITTING PDF PAGES [START] ******************\n"
	print "splitting pdf at %s into pages" % task.doc_id
	task.setStatus(412)

	from copy import deepcopy
	from lib.Worker.Models.cp_pdf import CompassPDF

	from conf import DEBUG
	from vars import ASSET_TAGS

	pdf = CompassPDF(_id=task.doc_id)
	if pdf is None:
		print "PDF IS NONE"
		print "\n\n************** SPLITTING PDF PAGES [ERROR] ******************\n"
		return

	from cStringIO import StringIO
	from PyPDF2 import PdfFileWriter

	from lib.Worker.Models.uv_task import UnveillanceTask
	from vars import MIME_TYPE_TASKS

	MAX_PAGES = 200

	next_task = {
		'task_path' : MIME_TYPE_TASKS['application/pdf'][1],
		'doc_id' : task.doc_id,
		'queue' : task.queue
	}

	pdf_reader = pdf.loadFile(pdf.file_name)
	if pdf_reader is None:
		print "PDF READER IS NONE"
		print "\n\n************** SPLITTING PDF PAGES [ERROR] ******************\n"
		return

	# get num pages
	total_pages = pdf_reader.getNumPages()
	if not hasattr(task, "num_pages"): task.num_pages = MAX_PAGES

	if total_pages > task.num_pages:
		print "THIS SHOULD BE SPLIT BEFORE CONTINUING!"

		count = done = 0
		out = PdfFileWriter()

		for x in xrange(0, total_pages):
			page = pdf_reader.getPage(x)

			if x != 0 and x % num_pages == 0:
				if DEBUG:
					print "max reached... let's close this doc (done = %d)" % done
					print "merging pages %d to %d to PDF" % (count, x)

				count = x
				done += 1

				new_pdf = StringIO()
				out.write(new_pdf)
				new_pdf.close()

				if pdf.addAsset(new_pdf.getvalue(), "doc_split_%d.pdf" % done,
					tags=[ASSET_TAGS['D_S'], ASSET_TAGS['AS_PDF']], description="Chunk %d of original document" % done):
					
					doc_split_task = deepcopy(next_task)
					doc_split_task.update({
						'split_file' : "doc_split_%d.pdf" % done,
						'split_index' : done
					})
					new_task = UnveillanceTask(inflate=doc_split_task)
					new_task.run()
	else:
		new_task = UnveillanceTask(inflate=deepcopy(next_task))
		new_task.run()


	task.finish()
	print "\n\n************** SPLITTING PDF PAGES [END] ******************\n"