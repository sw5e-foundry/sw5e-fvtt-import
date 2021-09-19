import sw5e.Equipment, utils.text
import re, json

class Tool(sw5e.Equipment.Equipment):
	def load(self, raw_item):
		super().load(raw_item)

	def process(self, old_item, importer):
		super().process(old_item, importer)

		self.action = 'action'

	def getImg(self):
		kwargs = {
			# 'item_type': self.equipmentCategory,
			'no_img': ('Unknown', 'Tool'),
			'default_img': 'systems/sw5e/packs/Icons/Kit/Demolitions%20Kit.webp',
			# 'plural': False
		}
		return super().getImg(**kwargs)

	def getDescription(self, importer):
		text = self.description
		return utils.text.markdownToHtml(text)

	def getToolType(self):
		tools = {
			"Antitoxkit": 'ant',
			"Archaeologist kit": 'arc',
			"Armormech's implements": 'armor',
			"Armstech's implements": 'arms',
			"Artificer's implements": 'arti',
			"Artist's implements": 'art',
			"Astrotech's implements": 'astro',
			"Audiotech's implements": 'aud',
			"Bioanalysis kit": 'bioa',
			"Biotech's implements": 'bio',
			"Brewer's kit": 'brew',
			"Chef's kit": 'chef',
			"Constructor's implements": 'con',
			"Cybertech's implements": 'cyb',
			"Demolitions kit": 'demo',
			"Disguise kit": 'disg',
			"Forgery kit": 'forg',
			"GamingSet": 'game',
			"Jeweler's implements": 'jew',
			"Mechanic's kit": 'mech',
			"Munitions kit": 'ammo',
			"MusicalInstrument": 'music',
			"Poisoner's kit": 'poi',
			"Scavenging kit": 'scav',
			"Security kit": 'secur',
			"Slicer's kit": 'slic',
			"Spicer's kit": 'spice',
			"Surveyor's implements": 'sur',
			"Synthweaver's implements": 'syn',
			"Tinker's implements": 'tin'
		}
		if self.name in tools: return tools[self.name], 'int'
		elif self.equipmentCategory in tools: return tools[self.equipmentCategory], 'cha'
		print(f'		Unable to recognize tool type for {self.name}, {self.equipmentCategory}')
		return '', 'int'

	def getData(self, importer):
		data = super().getData(importer)[0]

		data["data"]["toolType"], data["data"]["ability"] = self.getToolType()

		return [data]
