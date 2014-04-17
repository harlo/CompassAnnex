from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def splitPDFPages(task):
	print "\n\n************** SPLITTING PDF PAGES [START] ******************\n"
	print "splitting pdf at %s into pages" % task.doc_id
	task.setStatus(412)

	from lib.Worker.Models.cp_pdf import CompassPDF

	from conf import DEBUG
	from vars import ASSET_TAGS

	pdf = CompassPDF(_id=task.doc_id)
	if pdf is None:
		print "PDF IS NONE"
		print "\n\n************** SPLITTING PDF PAGES [ERROR] ******************\n"
		return

	from lib.Worker.Models.uv_task import UnveillanceTask
	from cStringIO import cStringIO
	from PyPDF2 import PdfFileReader, PdfFileWriter

	MAX_PAGES = 200

	# get num pages
	total_pages = pdf.getNumPages()
	if not hasattr(task, "num_pages"):
		task.num_pages = MAX_PAGES

	if total_pages > task.num_pages:
		print "THIS SHOULD BE SPLIT BEFORE CONTINUING!"

		count = done = 0
		out = PdfFileWriter()

		for x in xrange(0, total_pages):
			page = pdf.getPage(x)

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
					new_task = UnveillanceTask(inflate={
						'task_path' : MIME_TYPE_TASKS['PDF'][1],
						'doc_id' : task.doc_id,
						'queue' : task.queue,
						'split_file' : "doc_split_%d.pdf" % done
					})
					new_task.run()



	task.finish()
	print "\n\n************** SPLITTING PDF PAGES [END] ******************\n"
