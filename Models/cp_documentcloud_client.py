import requests, json

from conf import DEBUG, getConfig

class CompassDocumentCloudClient(object):
	def __init__(self, auth_str=None):
		if auth_str is not None:
			self.auth_str = auth_str
		
		self.setCompassProject()
	
	def setCompassProject(self):
		url = "projects.json"
		
		projects = self.sendDCRequest(url, "get")
		if projects is not None:
			for project in projects['projects']:
				if project['title'] == getConfig('documentcloud.proj_title'):
					self.project_id = project['id']
					return True
		
		if not hasattr(self, "project_id"):
			project = self.sendDCRequest(url, "post", data={
				'title' : getConfig('documentcloud.proj_title')
			})
			if DEBUG: print "new project:\n%s\n" % project
			return self.hasCompassProject()
		
		return False
	
	def download(self, endpoint):
		return sendDCRequest(endpoint, "get")
	
	def upload(self, document):
		from conf import UV_UUID
		
		url = "upload.json"
		try:
			data = {
				'file' : document.loadFile(document.file_name),
				'title' : document.file_name,
				'project' : self.project_id,
				'access' : "private",
				'data' : {
					'upload_source' : getConfig('documentcloud.proj_title'),
					'farm' : UV_UUID
				},
				'secure' : True
			}
		except Exception as e:
			if DEBUG:
				print "ERROR CREATING UPLOAD REQUEST: %s\n" % e
				return None

		return self.sendDCRequest(url, "post", data=data)
	
	def sendDCRequest(self, url, method, data=None):
		auth_str = ""
		if hasattr(self, "auth_str"):
			auth_str = self.auth_str
		
		url = "https://%sdocumentcloud.org/api/%s" % (auth_str, url)
		if method == "get":
			r = requests.get(url, data=json.dumps(data))
		elif method == "post":
			r = request.post(url, data=json.dumps(data))
			
		try:
			if DEBUG: print r.content
			return json.loads(r.content)
		except Exception as e:
			if DEBUG:
				print "ERROR SENDING DC REQUEST: %s\n" % e
				
		return None