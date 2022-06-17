import sw5e.Entity, sw5e.Advancement, utils.text
import re, json

class Species(sw5e.Entity.Item):
	def load(self, raw_species):
		super().load(raw_species)

		attrs = [
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
		for attr in attrs: setattr(self, f'raw_{attr}', utils.text.clean(raw_species, attr))

	def process(self, old_item, importer):
		super().process(old_item, importer)

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
				else: self.broken_links = True
			else:
				if self.foundry_id: print(f'		Unable to find feature {trait_data=}')
				self.broken_links = True
		if len(uids): advancements.append( sw5e.Advancement.ItemGrant(name="Traits", uids=uids, level=0, optional=True) )

		return advancements

	def getData(self, importer):
		data = super().getData(importer)[0]

		data["data"]["description"] = { "value": self.getDescription() }
		data["data"]["source"] = self.raw_contentSource
		data["data"]["-=traits"] = None
		data["data"]["identifier"] = utils.text.slugify(self.name, capitalized=False)
		data["data"]["advancement"] = [ adv.getData(importer) for adv in self.advancements ]
		data["data"]["skinColorOptions"] = { "value": self.raw_skinColorOptions}
		data["data"]["hairColorOptions"] = { "value": self.raw_hairColorOptions}
		data["data"]["eyeColorOptions"] = { "value": self.raw_eyeColorOptions}
		data["data"]["colorScheme"] = { "value": self.raw_colorScheme}
		data["data"]["distinctions"] = { "value": self.raw_distinctions}
		data["data"]["heightAverage"] = { "value": self.raw_heightAverage}
		data["data"]["heightRollMod"] = { "value": self.raw_heightRollMod}
		data["data"]["weightAverage"] = { "value": self.raw_weightAverage}
		data["data"]["weightRollMod"] = { "value": self.raw_weightRollMod}
		data["data"]["homeworld"] = { "value": self.raw_homeworld}
		data["data"]["slanguage"] = { "value": self.raw_language}
		data["data"]["-=damage"] = None
		data["data"]["-=armorproperties"] = None
		data["data"]["-=weaponproperties"] = None

		return [data]
