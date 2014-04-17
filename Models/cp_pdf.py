import os
from PyPDF2 import PdfFileReader

from lib.Worker.Models.uv_document import UnveillanceDocument
from lib.Core.vars import EmitSentinel
from conf import ANNEX_DIR, DEBUG

class CompassPDF(UnveillanceDocument, PdfFileReader):
	def __init__(self, _id=None, inflate=None):
		emit_sentinels = [EmitSentinel("pdf_reader", "PdfFileReader", None)]

		UnveillanceDocument.__init__(self, _id=_id, inflate=inflate, emit_sentinels=emit_sentinels)

	def loadFile(self, asset_path=None):
		if asset_path is None:
			if not self.getFile(self.file_name): return None
			try:
				PdfFileReader.__init__(self, file(os.path.join(ANNEX_DIR, self.file_name)))
				return True
			except Exception as e: return None

		return super(CompassPDF, self).loadFile(asset_path)


	def loadAsset(self, file_name):
		asset = self.getAsset(file_name)
		if asset is None: return None

		if hasattr(asset, 'tags') and ASSET_TAGS['AS_PDF'] in asset.tags:
			try:
				return PdfFileReader(file(os.path.join(ANNEX_DIR, self.base_path, file_name)))
			except Exception as e: return None

		return super(CompassPDF, self).loadFile(file_name)