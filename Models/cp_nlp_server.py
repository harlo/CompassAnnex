import jsonrpclib, os
from simplejson import loads
from fabric.api import local

from lib.Core.Utils.funcs import stopDaemon, startDaemon
from Utils.funcs import printAsLog
from conf import MONITOR_ROOT, DEBUG, getConfig

class CompassNLPServerHandler(object):
	def __init__(self):
		if DEBUG: print "initing nlp handler"

class CompassNLPServer(CompassNLPServerHandler):
	def __init__(self):
		if DEBUG: print "initing Stanford Core NLP Server"
		self.pid_file = os.path.join(MONITOR_ROOT, "nlp_svr.pid.txt")
		self.log_file = os.path.join(MONITOR_ROOT, "nlp_svr.log.txt")
		self.status_file = os.path.join(MONITOR_ROOT, "nlp_svr.status.txt")
		
		CompassNLPServerHandler.__init__(self)
	
	def startServer(self):
		self.svr_path = getConfig('nlp_server.path')
		self.svr_port = getConfig('nlp_server.port')
		
		cmd = "python %s -S %s" % (
			os.path.join(self.svr_path, "corenlp", "corenlp.py"),
			os.path.join(self.svr_path, getConfig('nlp_server.pkg')))
		
		start_server = local(cmd)

		if DEBUG: 
			print cmd
			print "STARTING NLP SERVER:\n%s" % start_server
		
		self.nlp_server = jsonrpclib.Server("http://localhost:%d" % self.svr_port)
		
		startDaemon(self.log_file, self.pid_file)
		with open(self.status_file, 'wb+') as status_file: status_file.write("True")
		while True: sleep(1)
	
	def stopServer(self)
		printAsLog("stopping NLP server")
		
		stopDaemon(self.pid_file, extra_pids_port=self.svr_port)
		with open(self.status_file, 'wb+') as status_file: status_file.write("False")