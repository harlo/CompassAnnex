import jsonrpclib, os, json, threading
from time import sleep
from multiprocessing import Process
from lib.Core.Utils.funcs import stopDaemon, startDaemon
from Utils.funcs import printAsLog
from conf import MONITOR_ROOT, DEBUG, getConfig

class CompassNLPServer(object):
	def __init__(self):
		if DEBUG: print "initing Stanford Core NLP Server"
		
		self.pid_file = os.path.join(MONITOR_ROOT, "nlp_svr.pid.txt")
		self.log_file = os.path.join(MONITOR_ROOT, "nlp_svr.log.txt")
		self.status_file = os.path.join(MONITOR_ROOT, "nlp_svr.status.txt")
		
		if not self.getStatus():
			p = Process(target=self.startServer)
			p.start()
	
	def getStatus(self):
		try:
			with open(self.status_file, 'rb') as SF: return bool(SF.read().strip())
		except IOError as e:
			if DEBUG: print e
		
		return False
			
	def startServer(self):
		from fabric.api import local
		
		self.svr_path = getConfig('nlp_server.path')
		self.svr_port = getConfig('nlp_server.port')
		
		cmd = "python %s -S %s -p %d" % (
			os.path.join(self.svr_path, "corenlp", "corenlp.py"),
			os.path.join(self.svr_path, getConfig('nlp_server.pkg')),
			getConfig('nlp_server.port'))
		
		start_server = local(cmd)

		if DEBUG: 
			print cmd
			print "STARTING NLP SERVER:\n%s" % start_server
		
		self.nlp_server = jsonrpclib.Server("http://localhost:%d" % self.svr_port)
		
		startDaemon(self.log_file, self.pid_file)
		with open(self.status_file, 'wb+') as status_file: status_file.write("True")
		while True: sleep(1)
	
	def stopServer(self):
		printAsLog("stopping NLP server")
		
		stopDaemon(self.pid_file, extra_pids_port=self.svr_port)
		with open(self.status_file, 'wb+') as status_file: status_file.write("False")
		
		try:
			del self.nlp_server
		except Exception as e:
			print "error stopping NLP server\n%s" % e
	
	class NLPRequest(threading.Thread):
		def __init__(self, server, texts, blocking=False):
			self.blocking = blocking
			self.server = server
			self.texts = texts
		
		def getResult(self): pass
	
	class Tokenizer(NLPRequest):
		def __init__(self, texts):
			super(Tokenier, self).__init__(texts, blocking=True)
		
		def run(self):
			print "DOING TOKENIZER"
			if type(texts) is not list: texts = [texts]
			for text in texts: self.server.send(text)
		
		def getResult(self):
			try:
				return self.server.getAll()
			except Exception as e:
				if DEBUG:
					print "I HAVE NO CLUE ABOUT THIS SERVER"
			
			return None
	
	def sendNLPRequest(self, query):
		if not self.getStatus():
			if DEBUG: print "starting NLP server before requesting"
			p = Process(target=self.startServer)
			p.start()
			
			starts = 0
			while not self.getStatus():
				if DEBUG: print "Still waiting for NLP server to become available..."
				starts += 1
				sleep(5)
				
				if starts >= 24: 
					if DEBUG: print "Sorry, this server is just never going to start."
					return None
				
		if 'method' not in query.keys() or 'txt' not in query.keys():
			if DEBUG: print "no method or text.  nothing to do"
			return None
		
		if query['method'] == "tokenize": return self.Tokenizer(self.nlp_server, txt)
		
		return None
			