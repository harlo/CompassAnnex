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

	import os
	from nltk.tag.stanford import NERTagger
	from conf import getConfig
	from lib.Core.Utils.funcs import cleanLine

	st = NERTagger(
		os.path.join(getConfig('nlp_ner_base'), 
			"classifiers", "english.all.3class.distsim.crf.ser.gz"),
		os.path.join(getConfig('nlp_ner_base'), "stanford-ner.jar"))

	entities = {}

	pages = [text for text in texts]
	for i, page in enumerate(pages):
		if page is None: continue

		print "LEMMATIZING PAGE %d of %d" % (i, len(pages))
		try:
			lemmas = st.tag(cleanLine(page).split())
		except Exception as e:
			print "\n\n************** %s [WARN] ******************\n" % task_tag
			print e
			continue

		if len(lemmas) == 0: continue

		if DEBUG: print "page has %d lemmas" % len(lemmas)

		index = 0
		current_entity = []
		last_pos = "O"

		while True:
			try:
				entity = lemmas[index]
			except Exception as e:
				entities = updateEntities(entities, current_entity, last_pos, i)				
				break

			if entity[1] not in ["O"]:
				print entity, last_pos

				if entity[1] != last_pos:
					entities = updateEntities(entities, current_entity, entity[1], i)
					current_entity = []

				current_entity.append(entity[0])
			else:
				entities = updateEntities(entities, current_entity, last_pos, i)
				current_entity = []

			last_pos = entity[1]
			index += 1

	if DEBUG: print entities
	if len(entities.keys()) > 0:
		ner_entity_path = doc.addAsset(entities, "stanford-ner_entities.json", as_literal=False,
			description="Entities as per Stanford-NER Tagger (via NLTK)",
			tags=[ASSET_TAGS['STANFORD_NER_ENTITIES'], ASSET_TAGS['CP_ENTITIES']])

		if ner_entity_path is not None:
			doc.addFile(ner_entity_path, None, sync=True)

	doc.addCompletedTask(task.task_path)
	task.routeNext()
	task.finish()
	print "\n\n************** %s [END] ******************\n" % task_tag

def updateEntities(entities, current_entity, last_pos, page):
	from conf import DEBUG

	if len(current_entity) != 0:
		entity = " ".join(current_entity)

		if last_pos.lower() not in entities.keys():
			entities[last_pos.lower()] = []
		
		if entity not in entities[last_pos.lower()]:
			entities[last_pos.lower()].append(entity)

		if DEBUG: 
			print "ENTITY FOUND: %s" % entity

		if "uv_page_map" not in entities.keys():
			entities["uv_page_map"] = []

		in_page_map = [e for e in entities['uv_page_map'] if e['entity'] == entity]
		if len(in_page_map) != 1:
			entities['uv_page_map'].append({
				'entity' : entity,
				'pages' : [page],
				'count' : 1
			})
		else:
			if page not in in_page_map[0]['pages']: in_page_map[0]['pages'].append(page)
			in_page_map[0]['count'] += 1

		

	return entities