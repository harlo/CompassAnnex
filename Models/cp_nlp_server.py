import jsonrpclib, os
from simplejson import loads
from fabric.api import local

from lib.Core.Utils.funcs import stopDaemon, startDaemon
from Utils.funcs import printAsLog
from conf import MONITOR_ROOT, DEBUG, getConfig

class CompassNLPServer(object):
	def __init__(self):
		if DEBUG: print "initing Stanford Core NLP Server"
		
		self.pid_file = os.path.join(MONITOR_ROOT, "nlp_svr.pid.txt")
		self.log_file = os.path.join(MONITOR_ROOT, "nlp_svr.log.txt")
		self.status_file = os.path.join(MONITOR_ROOT, "nlp_svr.status.txt")
	
	def tokenize(self, nlp_server, texts, blocking=True):
		if type(texts) is not list: texts = [texts]
		
		for text in texts: nlp_server.send(text)
		
		if blocking: return nlp_server.getAll()
		else: return True
		# TODO: fail states.
			
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
		
		try:
			del self.nlp_server
		except Exception as e:
			print "error stopping NLP server\n%s" % e
	
	def sendNLPRequest(self, query):
		if not hasattr(self, "nlp_server"):
			if DEBUG: print "starting NLP server before requesting"
			self.startServer()
			sleep(5)
		
		# TODO: if server is unusable		
		return None
			