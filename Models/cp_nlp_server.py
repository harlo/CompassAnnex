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
		
		p = Process(target=self.startServer)
		p.start()
			
	def startServer(self):
		from fabric.api import local, settings
		
		this_dir = os.getcwd()
		cmd = "java -mx1000m -cp stanford-ner.jar edu.stanford.nlp.ie.NERServer -loadClassifier classifiers/english.all.3class.distsim.crf.ser.gz -port %d -outputFormat inlineXML" % getConfig('nlp_server.port')
		
		if DEBUG: 
			print "STARTING NLP SERVER:"
			print cmd
		
		os.chdir(getConfig('nlp_ner_base'))
		with settings(warn_only=True):
			local("kill $(lsof -t -i:%d)" % getConfig('nlp_server.port'))
			start_cmd = local(cmd)
		
		print start_cmd
		
		startDaemon(self.log_file, self.pid_file)
		while True: sleep(1)
	
	def stopServer(self):
		printAsLog("stopping NLP server")
		stopDaemon(self.pid_file, extra_pids_port=getConfig('nlp_server.port'))
		
		try:
			del self.nlp_server
		except Exception as e:
			print "error stopping NLP server\n%s" % e