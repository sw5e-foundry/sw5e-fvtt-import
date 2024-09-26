import sw5e.Entity, utils.object

class Template(sw5e.Entity.Entity):
	def load(self, raw_entity):
		super().load(raw_entity)
		for (path, key) in self.dataMap().items():
			fooName = f'get{utils.text.capitalCase(key)}'
			foo = getattr(self, fooName)
			val = foo()
			setattr(self, key, val)

	def processTemplates(self, importer):
		super().processTemplates(importer)
		for (path, key) in self.dataMap().items():
			fooName = f'process{utils.text.capitalCase(key)}'
			foo = getattr(self, fooName, None)
			if foo: foo(importer)

	# def getProperty(self):
	# 	raise NotImplementedError()
	# 	return None

	# def processProperty(self, importer):
	# 	pass

	def dataMap(self):
		return {
			# 'system.property': 'property',
		}

	def getData(self, importer):
		datas = super().getData(importer)

		for data in datas:
			for (path, key) in self.dataMap().items():
				val = None
				fooName = f'getData{utils.text.capitalCase(key)}'
				if foo := getattr(self, fooName, None):
					val = foo(importer)
				else:
					val = getattr(self, key)
				if val != None: utils.object.setProperty(data, path, val, force=True)

		return datas
