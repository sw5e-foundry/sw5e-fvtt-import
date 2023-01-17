def getProperty(obj, path, default=None):
	parts = path.split('.')
	for part in parts:
		if part not in obj: return default
		obj = obj[part]
	return obj

def setProperty(obj, path, value, force=False):
	parts = path.split('.')
	for part in parts[:-1]:
		if part not in obj and force: obj[part] = {}
		obj = obj[part]
	if (force == 'weak' and obj[parts[-1]] == None) or (force != 'weak'): obj[parts[-1]] = value
