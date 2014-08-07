from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def startNLPServer(task):
	task_tag = "NLP CORE SERVER START"
	print "\n\n************** %s [START] ******************\n" % task_tag
	task.setStatus(412)
	
	from lib.Worker.Models.cp_nlp_server import CompassNLPServer
	
	nlp_server = CompassNLPServer()	
	task.finish()
	print "\n\n************** %s [END] ******************\n" % task_tag