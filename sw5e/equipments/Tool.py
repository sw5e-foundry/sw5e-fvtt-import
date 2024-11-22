import sw5e.Equipment, utils.text
import re, json

class Tool(sw5e.Equipment.Equipment):
	def load(self, raw_item):
		super().load(raw_item)

	def process(self, importer):
		super().process(importer)

	def getActivation(self):
		return 'action'

	def getImg(self, importer=None):
		kwargs = {
			# 'item_type': self.raw_equipmentCategory,
			'no_img': ('Unknown', 'Tool'),
			'default_img': 'modules/sw5e/icons/packs/Kit/DemolitionsKit.webp',
			# 'plural': False
		}
		return super().getImg(importer=importer, **kwargs)

	def getData(self, importer):
		data = super().getData(importer)[0]

		utils.object.setProperty(data, 'system.ability', '')
		utils.object.setProperty(data, 'system.chatFlavor', '')
		utils.object.setProperty(data, 'system.proficient', None)
		utils.object.setProperty(data, 'system.bonus', 0)

		return [data]

	############################
	#    Template Functions    #
	############################

	# templates.Activities

	# templates.ItemDescription
	def getDescription(self):
		text = self.raw_description
		return utils.text.markdownToHtml(text)

	# templates.Identifiable

	# template.ItemType
	def getCategory(self):
		tools = {
			"GamingSet": 'game',
			"MusicalInstrument": 'music',
			"ArtisanImplements": 'art',
			"SpecialistsKit": 'kit',
		}
		category = self.raw_equipmentCategory
		if self.name.find('implements') != -1: category = 'ArtisanImplements'
		elif self.name.find('kit') != -1: category = 'SpecialistsKit'

		if category in tools: return tools[category]
		elif self.name != 'Tool': print(f'		Unable to recognize tool type for {self.name}, {category}')
		return None

	# template.PhysicalItem

	# templates.EquippableItem

#