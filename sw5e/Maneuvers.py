import sw5e.Feature, utils.text
import re, json

class Maneuvers(sw5e.Feature.BaseFeature):
	############################
	#      Load Functions      #
	############################

	def getAttrs(self):
		return super().getAttrs() + [ "metadata", "type", "eTag" ]

	def loadConsume(self):
		return {
			"scaling": {
				"allowed": False,
				"max": None,
			},
			"spellSlot": False,
			"targets": [
				{
					"scaling": {
						"formula": '',
						"mode": '',
					},
					"target": 'superiority.dice.value',
					"type": 'attribute',
					"value": 1,
				},
			],
		}

	def loadFeatType(self):
		return None, None

	############################
	#    Process Functions     #
	############################

	############################
	#      Other Functions     #
	############################

	def getType(self):
		return "sw5e.maneuver"

	def getImg(self, importer=None):
		name = utils.text.slugify(self.name)
		return f'modules/sw5e/icons/packs/Maneuvers/{name}.webp'

	def getAction(self):
		return utils.text.getAction(self.raw_text, self.name, rolled_formula='1d@superiority.die')

	def getData(self, importer):
		data = super().getData(importer)[0]

		data["system"]["type"] = { "value": self.raw_type.lower() }

		return [data]

	def getFile(self, importer):
		return f'Maneuver'

	############################
	#    Template Functions    #
	############################
