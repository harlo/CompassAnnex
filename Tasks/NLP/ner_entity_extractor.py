from __future__ import absolute_import

from vars import CELERY_STUB as celery_app

@celery_app.task
def extractNEREntities(task):
	task_tag = "NER ENTITY EXTRACTION"
	print "\n\n************** %s [START] ******************\n" % task_tag
	print "TOKENIZING TEXT DOCUMENT at %s" % task.doc_id
	task.setStatus(412)

	from lib.Worker.Models.uv_document import UnveillanceDocument

	from conf import DEBUG
	from vars import ASSET_TAGS

	doc = UnveillanceDocument(_id=task.doc_id)
	if doc is None:
		print "DOC IS NONE"
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		return

	from json import loads

	try:
		texts = loads(doc.loadAsset("doc_texts.json"))
	except Exception as e:
		print "ERROR GETTING DOC-TEXTS: %s" % e
		print "\n\n************** %s [ERROR] ******************\n" % task_tag
		return

	from nltk.tag.stanford import NERTagger
	from conf import getConfig
	from lib.Core.Utils.funcs import cleanAndSplitLine

	st = NERTagger(
		os.path.join(getConfig('nlp_ner_base'), 
			"classifiers", "english.all.3class.distsim.crf.ser.gz"),
		os.path.join(getConfig('nlp_ner_base'), "stanford-ner.jar"))

	entities = {}

	for sentence in [cleanAndSplitLine(text) for text in texts if text is not None]:
		lemmas = st.tag(sentence)
		if len(lemmas) == 0: continue

		last_pos = "O"
		index = 0
		current_entity = []

		while last_pos is not None:
			try:
				entity = lemmas[index]
			except Exception as e:
				last_pos = None
				break

			if entity[1] not in ["O"]:
				if entity[1] != last_pos:
					if(len(current_entity) > 0):
						if entity[1].lower() not in entities.keys():
							entities[entity[1].lower()] = []

						entities[entity[1].lower()].push(" ".join(current_entity))
						current_entity = []

				current_entity.push(entity[0])
			else:
				if(len(current_entity) > 0): current_entity = []


			last_pos = entity[1]
			index += 1

	if DEBUG: print entities
	if len(entities.keys() > 0):
		ner_entity_path = doc.addAsset(entities, "stanford-ner_entities.json", as_literal=False,
			description="Entities as per Stanford-NER Tagger (via NLTK)",
			tags=[ASSET_TAGS['STANFORD_NER_ENTITIES'], ASSET_TAGS['CP_ENTITIES']])

		if ner_entity_path is not None:
			doc.addFile(ner_entity_path, None, sync=True)

	doc.addCompletedTask(task.task_path)
	task.routeNext()
	task.finish()
	print "\n\n************** %s [END] ******************\n" % task_tag