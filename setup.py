import os, json
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

	if not os.path.exists(os.path.join("lib","stanford-corenlp", config['nlp_pkg'])):
		os.chdir(os.path.join("lib", "stanford-corenlp"))
		with settings(warn_only=True):
			local("wget http://nlp.stanford.edu/software/%s.zip" % config['nlp_pkg'])
			local("unzip %s.zip" % config['nlp_pkg'])
		os.chdir(base_dir)
	else:
		print "Stanford NLP Package %s already downloaded. skipping..." % config['nlp_pkg']
	
	if not os.path.exists(os.path.join("lib", "stanford-ner-2014-06-16")):
		os.chdir(os.path.join(base_dir, "lib"))
		with settings(warn_only=True):
			local("wget http://nlp.stanford.edu/software/stanford-ner-2014-06-16.zip")
			local("unzip stanford-ner-2014-06-16.zip")
			local("rm stanford-ner-2014-06-16.zip")
		os.chdir(base_dir)
	else:
		print "Stanford NER Package already downloaded. skipping..."

	gensim_lib = os.path.join(base_dir, "lib", "gensim_lib")
	if not os.path.exists(gensim_lib):
		with settings(warn_only=True):
			local("mkdir %s" % gensim_lib)

	with open(os.path.join(base_dir, "lib", "peepdf", "batch.txt"), 'wb+') as BATCH:
		BATCH.write("info\nmetadata\ntree\n")
	
	stopwords = {
		"english" : [
			"a", "about", "above", "above", "across", "after", 
			"afterwards", "again", "against", "all", "almost", 
			"alone", "along", "already", "also","although","always","am",
			"among", "amongst", "amoungst", "amount", "an", 
			"and", "another", "any","anyhow","anyone","anything",
			"anyway", "anywhere", "are", "around", "as", "at",
			"back","be","became", "because","become","becomes",
			"becoming", "been", "before", "beforehand", "behind", 
			"being", "below", "beside", "besides", "between", 
			"beyond", "bill", "both", "bottom","but", "by", "call", 
			"can", "cannot", "cant", "co", "con", "could", "couldnt", 
			"cry", "de", "describe", "detail", "do", "done", "down", 
			"due", "during", "each", "eg", "eight", "either", "eleven",
			"else", "elsewhere", "empty", "enough", "etc", "even", 
			"ever", "every", "everyone", "everything", "everywhere", 
			"except", "few", "fifteen", "fify", "fill", "find", 
			"fire", "first", "five", "for", "former", "formerly", 
			"forty", "found", "four", "from", "front", "full", 
			"further", "get", "give", "go", "had", "has", 
			"hasnt", "have", "he", "hence", "her", "here", 
			"hereafter", "hereby", "herein", "hereupon", "hers", 
			"herself", "him", "himself", "his", "how", "however", 
			"hundred", "ie", "if", "in", "inc", "indeed", "interest", 
			"into", "is", "it", "its", "itself", "keep", "last", 
			"latter", "latterly", "least", "less", "ltd", "made", 
			"many", "may", "me", "meanwhile", "might", "mill", "mine", 
			"more", "moreover", "most", "mostly", "move", "much", 
			"must", "my", "myself", "name", "namely", "neither", 
			"never", "nevertheless", "next", "nine", "no", "nobody", 
			"none", "noone", "nor", "not", "nothing", "now", 
			"nowhere", "of", "off", "often", "on", "once", "one", 
			"only", "onto", "or", "other", "others", "otherwise", 
			"our", "ours", "ourselves", "out", "over", "own","part", 
			"per", "perhaps", "please", "put", "rather", "re", "same", 
			"see", "seem", "seemed", "seeming", "seems", "serious", 
			"several", "she", "should", "show", "side", "since", 
			"sincere", "six", "sixty", "so", "some", "somehow", 
			"someone", "something", "sometime", "sometimes", 
			"somewhere", "still", "such", "system", "take", "ten", 
			"than", "that", "the", "their", "them", "themselves", 
			"then", "thence", "there", "thereafter", "thereby", 
			"therefore", "therein", "thereupon", "these", "they", 
			"thickv", "thin", "third", "this", "those", "though", 
			"three", "through", "throughout", "thru", "thus", "to",
			"together", "too", "top", "toward", "towards", "twelve", 
			"twenty", "two", "un", "under", "until", "up", "upon", 
			"us", "very", "via", "was", "we", "well", "were", "what", 
			"whatever", "when", "whence", "whenever", "where", "whereafter", 
			"whereas", "whereby", "wherein", "whereupon", "wherever", 
			"whether", "which", "while", "whither", "who", "whoever", 
			"whole", "whom", "whose", "why", "will", "with", "within",
			"without", "would", "yet", "you", "your", "yours", 
			"yourself", "yourselves", "the"
		]
	}
	
	with open(os.path.join(base_dir, "lib", "stanford-corenlp", "stopwords.json"), 'wb+') as STOPWORDS:
		STOPWORDS.write(json.dumps(stopwords))
	
	with open(os.path.join(conf_dir, "annex.config.yaml"), 'ab') as CONF:
		CONF.write("vars_extras: %s\n" % os.path.join(base_dir, "vars.json"))
		CONF.write("nlp_server.path: %s\n" % os.path.join(
			base_dir, "lib", "starnford-corenlp"))
		CONF.write("nlp_server.port: %d\n" % config['nlp_port'])
		CONF.write("nlp_server.pkg: %s\n" % config['nlp_pkg'])
		CONF.write("nlp_ner_base: %s\n" % os.path.join(base_dir, "lib", "stanford-ner-2014-06-16"))
		CONF.write("compass.peepdf.root: %s\n" % os.path.join(
			base_dir, "lib", "peepdf", "peepdf.py"))
		CONF.write("compass.peepdf.batch: %s\n" % os.path.join(
			base_dir, "lib", "peepdf", "batch.txt"))
		CONF.write("documentcloud.proj_title: Compass v1\n")
		CONF.write("compass.gensim.training_data: %s\n" % gensim_lib)

	initial_tasks = []

	try:
		with open(os.path.join(conf_dir, "initial_tasks.json"), 'rb') as I_TASKS:
			initial_tasks.extend(json.loads(I_TASKS.read()))
	except IOError as e: pass

	initial_tasks.append({
		'task_path' : "NLP.gensim_dictionary.buildGensimDictionary",
		'queue' : os.getenv('UV_UUID')
	})

	initial_tasks.append({
		'task_path' : "NLP.start_server.startNLPServer",
		'queue' : os.getenv('UV_UUID')
	})

	with open(os.path.join(conf_dir, "initial_tasks.json"), 'wb+') as I_TASKS:
		I_TASKS.write(json.dumps(initial_tasks))
	
	exit(0)