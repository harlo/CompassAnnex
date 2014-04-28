import os
from PyPDF2 import PdfFileReader

from lib.Worker.Models.uv_document import UnveillanceDocument
from conf import ANNEX_DIR, DEBUG

class CompassPDF(UnveillanceDocument):
	def __init__(self, _id=None, inflate=None):
		super(CompassPDF, self).__init__(_id=_id, inflate=inflate)

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
		asset = self.getAsset(file_name)
		if asset is None: return None

		if hasattr(asset, 'tags') and ASSET_TAGS['AS_PDF'] in asset.tags:
			try:
				return PdfFileReader(file(os.path.join(ANNEX_DIR, self.base_path, file_name)))
			except Exception as e:
				if DEBUG: print e
				return None

		return super(CompassPDF, self).loadFile(file_name)