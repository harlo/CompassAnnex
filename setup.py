import os
from fabric.operations import prompt
from fabric.api import local, settings

from lib.Annex.setup import locateLibrary

if __name__ == "__main__":
	base_dir = os.getcwd()
	conf_dir = os.path.join(base_dir, "lib", "Annex", "conf")
	
	config = {}
	print "****************************************"
	try:
		with open(os.path.join(conf_dir, "unveillance.secrets.json"), 'rb') as SECRETS:
			config.update(json.loads(SECRETS.read()))
	except Exception as e:
		print "no config file found.  please fill out the following:"
	
	if 'nlp_pkg' not in config:
		print "Which Stanford NLP Package should the Annex use?"
		config['nlp_pkg'] = prompt("[DEFAULT stanford-corenlp-full-2014-01-04]")
	
	if len(config['nlp_pkg']) == 0:
		config['nlp_pkg'] = "stanford-corenlp-full-2014-01-04"
		
	if 'nlp_port' not in config:
		print "What port should the Stanford NLP Package run on?"
		config['nlp_port'] = prompt("[DEFAULT 8887]")
	
	if type(config['nlp_port']) is not int:
		config['nlp_port'] = 8887
		
	os.chdir(os.path.join("lib", "stanford-corenlp"))
	with settings(warn_only=True):
		local("wget http://nlp.stanford.edu/software/%s.zip" % config['nlp_pkg'])
		local("unzip %s.zip" % config['nlp_pkg'])
	os.chdir(base_dir)
	
	with open(os.path.join(base_dir, "lib", "peepdf", "batch.txt"), 'wb+') as BATCH:
		BATCH.write("info\nmetadata\ntree\n")
	
	with open(os.path.join(conf_dir, "annex.config.yaml"), 'ab') as CONF:
		CONFIG.write("vars_extras: %s\n" % os.path.join(base_dir, "vars.json"))
		CONF.write("nlp_server.path: %s\n" % os.path.join(
			base_dir, "lib", "starnford-corenlp"))
		CONF.write("nlp_server.port: %d\n" % config['nlp_port'])
		CONF.write("nlp_server.pkg: %s\n" % config['nlp_pkg'])
		CONF.write("compass.peepdf.root: %s\n" % os.path.join(
			base_dir, "lib", "peepdf", "peepdf.py"))
		CONF.write("compass.peepdf.batch: %s\n" % os.path.join(
			base_dir, "lib", "peepdf", "batch.txt"))
	
	exit(0)