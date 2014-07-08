import jsonrpclib, os, json, threading, requests
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
		
		if not self.getStatus():
			p = Process(target=self.startServer)
			p.start()
	
	def getStatus(self):
		try:
			server_port = getConfig('nlp_server.port')
			r = requests.get("http://localhost:%d" % server_port)
			if r.status_code == 501:
				self.nlp_server = jsonrpclib.Server("http://localhost:%d" % server_port)
				return True
		except IOError as e: pass
		
		return False
			
	def startServer(self):
		from fabric.api import local, settings
		
		server_path = getConfig('nlp_server.path')
		
		cmd = "python %s -S %s -p %d" % (
			os.path.join(server_path, "corenlp", "corenlp.py"),
			os.path.join(server_path, getConfig('nlp_server.pkg')),
			getConfig('nlp_server.port'))
		
		if DEBUG: 
			print "STARTING NLP SERVER:"
			print cmd
		
		with settings(warn_only=True):
			start_cmd = local(cmd)
	
	def stopServer(self):
		printAsLog("stopping NLP server")
		stopDaemon(self.pid_file, extra_pids_port=getConfig('nlp_server.port'))
		
		try:
			del self.nlp_server
		except Exception as e:
			print "error stopping NLP server\n%s" % e
	
	def tokenize(self, texts):
		if type(texts) is not list: texts = [texts]
		
		tokenized = []
		for text in texts: 
			printAsLog("Attempting to tokenize:\n%s..." % text[:135])

			try:
				parse = self.nlp_server.parse(text)
				print type(parse)
				tokenized.append(json.loads(parse))
			except Exception as e:
				if DEBUG: print e
				continue
		
		if len(tokenized) > 0: return tokenized
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
		
		try:
			print "sending text:"
			print type(query['txt'])
			
			if query['method'] == "tokenize":
				return self.tokenize(query['txt'])
				
		except AttributeError as e: pass
		
		return None
			