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

	pdf_reader = pdf.loadFile(pdf.file_name)
	if pdf_reader is None:
		print "PDF READER IS NONE"
		print "\n\n************** SPLITTING PDF PAGES [ERROR] ******************\n"
		return

	# get num pages
	pdf.total_pages = pdf_reader.getNumPages()
	pdf.save()

	if not hasattr(task, "max_pages"): task.max_pages = MAX_PAGES

	if pdf.total_pages > task.max_pages:
		print "THIS SHOULD BE SPLIT BEFORE CONTINUING!"

		count = done = 0
		out = PdfFileWriter()

		for x in xrange(0, pdf.total_pages):
			page = pdf_reader.getPage(x)
new_pdf.close()
			if x != 0 and x % task.max_pages == 0:
				if DEBUG:
					print "max reached... let's close this doc (done = %d)" % done
					print "merging pages %d to %d to PDF" % (count, x)

				count = x
				done += 1

				new_pdf = StringIO()
				out.write(new_pdf)
				new_pdf.close()

				split_asset_path = pdf.addAsset(new_pdf.getvalue(), "doc_split_%d.pdf" % done,
					tags=[ASSET_TAGS['D_S'], ASSET_TAGS['AS_PDF']], description="Chunk %d of original document" % done)

				del out
				out = PdfFileWriter()

			out.addPage(page)
			count += 1
	
		del out


	pdf.addCompletedTask(task.task_path)
	task.routeNext()
	task.finish()
	print "\n\n************** SPLITTING PDF PAGES [END] ******************\n"