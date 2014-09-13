import os
from PyPDF2 import PdfFileReader

from lib.Worker.Models.uv_document import UnveillanceDocument
from conf import ANNEX_DIR, DEBUG
from vars import ASSET_TAGS

class CompassPDF(UnveillanceDocument):
	def __init__(self, _id=None, inflate=None):
		super(CompassPDF, self).__init__(_id=_id, inflate=inflate)

	def hasParts(self):
		if self.getAssetsByTagName(ASSET_TAGS['AS_PDF']) is not None:
			return True

		return False

	def getParts(self):
		if self.hasParts():
			return [c['file_name'] for c in self.getAssetsByTagName(ASSET_TAGS['AS_PDF'])]
		return None


	def loadFile(self, asset_path):
		if asset_path == self.file_name:
			if not self.getFile(self.file_name): return None
			try:
				return PdfFileReader(file(os.path.join(ANNEX_DIR, self.file_name)))
			except Exception as e:
				if DEBUG: print e
				return None

		return super(CompassPDF, self).loadFile(asset_path)


	def loadAsset(self, file_name):
		print "LOADING ASSET %s AS PDF:" % file_name
		asset = self.getAsset(file_name)
		print asset

		if asset is None: return None

		if 'tags' in asset[0].keys() and ASSET_TAGS['AS_PDF'] in asset[0]['tags']:
			try:
				return PdfFileReader(asset[1])
			except Exception as e:
				if DEBUG: print e
				return None

		return super(CompassPDF, self).loadFile(file_name)