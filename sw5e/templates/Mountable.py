from sw5e.templates import Template
import utils.object

class Mountable(Template):
	def dataMap(self):
		return {
			**super().dataMap(),
			# '?': '?'
		}
