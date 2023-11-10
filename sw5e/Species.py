import sw5e.Entity, sw5e.Advancement, utils.text
import re, json

class Species(sw5e.Entity.Item):
	def getAttrs(self):
		return super().getAttrs() + [
			"skinColorOptions",
			"hairColorOptions",
			"eyeColorOptions",
			"distinctions",
			"heightAverage",
			"heightRollMod",
			"weightAverage",
			"weightRollMod",
			"homeworld",
			"flavorText",
			"colorScheme",
			"manufacturer",
			"language",
			"traits",
			"abilitiesIncreased",
			"imageUrls",
			"size",
			"halfHumanTableEntries",
			"features",
			"contentTypeEnum",
			"contentType",
			"contentSourceEnum",
			"contentSource",
			"partitionKey",
			"timestamp",
			"rowKey",
		]

	def process(self, importer):
		super().process(importer)

		self.advancements = self.getAdvancements(importer)

	def getImg(self, importer=None):
		name = utils.text.slugify(self.name)
		return f'systems/sw5e/packs/Icons/Species/{name}.webp'

	def getDescription(self):
		return utils.text.markdownToHtml(self.raw_flavorText)

	def getAdvancements(self, importer):
		advancements = []

		uids = []
		for trait in self.raw_traits:
			trait_data = { "name": trait["name"], "source": 'Species', "sourceName": self.name, "level": None }
			if trait := importer.get('feature', data=trait_data):
				if trait.foundry_id: uids.append(f'Compendium.sw5e.speciesfeatures.{trait.foundry_id}')
				else: self.broken_links += ['no foundry id']
			else:
				if self.foundry_id: print(f'		Unable to find feature {trait_data=}')
				self.broken_links += ['cant find trait']
		if len(uids): advancements.append( sw5e.Advancement.ItemGrant(name="Traits", uids=uids, level=0, optional=True) )

		# TODO: Change this once/if we get the ability to restrict the choices you can spend points on
		fixed = {
			abl["abilities"][0][:3].lower(): abl["amount"]
			for abl in self.raw_abilitiesIncreased[0]
			if len(abl["abilities"]) == 1 and abl["abilities"][0][:3].lower() != 'any'
		}
		points = sum([
			abl["amount"]
			for abl in self.raw_abilitiesIncreased[0]
			if len(abl["abilities"]) != 1
		]) + sum([
			(abl["amount"] * utils.text.toInt(abl["abilities"][0][3:].strip(), allowWords=True, default=1))
			for abl in self.raw_abilitiesIncreased[0]
			if len(abl["abilities"]) == 1 and abl["abilities"][0][:3].lower() == 'any'
		])
		advancements.append( sw5e.Advancement.AbilityScoreImprovement(level=0, fixed=fixed, points=points) )

		return advancements

	def getData(self, importer):
		data = super().getData(importer)[0]

		data["system"]["description"] = { "value": self.getDescription() }
		data["system"]["source"] = self.raw_contentSource
		data["system"]["-=traits"] = None
		data["system"]["identifier"] = utils.text.slugify(self.name, capitalized=False)
		data["system"]["advancement"] = [ adv.getData(importer) for adv in self.advancements ]
		data["system"]["skinColorOptions"] = { "value": self.raw_skinColorOptions}
		data["system"]["hairColorOptions"] = { "value": self.raw_hairColorOptions}
		data["system"]["eyeColorOptions"] = { "value": self.raw_eyeColorOptions}
		data["system"]["colorScheme"] = { "value": self.raw_colorScheme}
		data["system"]["distinctions"] = { "value": self.raw_distinctions}
		data["system"]["heightAverage"] = { "value": self.raw_heightAverage}
		data["system"]["heightRollMod"] = { "value": self.raw_heightRollMod}
		data["system"]["weightAverage"] = { "value": self.raw_weightAverage}
		data["system"]["weightRollMod"] = { "value": self.raw_weightRollMod}
		data["system"]["homeworld"] = { "value": self.raw_homeworld}
		data["system"]["slanguage"] = { "value": self.raw_language}
		data["system"]["-=damage"] = None
		data["system"]["-=armorproperties"] = None
		data["system"]["-=weaponproperties"] = None

		return [data]
