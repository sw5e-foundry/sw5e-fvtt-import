import sw5e.Entity, utils.object

class Mountable(sw5e.Entity.Entity):
	def load(self, raw_entity):
		super().load(raw_entity)

	def getData(self, importer):

		data = super().getData(importer)[0]

		utils.object.setProperty(data, 'system.?', None, force=True)

		return [data]
