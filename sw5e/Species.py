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

		self.features = self.getFeatures(importer)
		self.creature_type = self.getCreatureType()
		self.speeds = self.getSpeeds()
		self.traits = self.getTraits()
		self.advancements = self.getAdvancements(importer)

	def getImg(self, importer=None):
		name = utils.text.slugify(self.name)
		return f'systems/sw5e/packs/Icons/Species/{name}.webp'

	def getDescription(self):
		return utils.text.markdownToHtml(self.raw_flavorText)

	def getFeatures(self, importer):
		features = []
		for trait in self.raw_traits:
			trait_data = { "name": trait["name"], "source": 'Species', "sourceName": self.name, "level": None }
			if trait := importer.get('feature', data=trait_data):
				if trait.foundry_id: features.append(trait)
				else: self.broken_links += ['no foundry id']
			else:
				if self.foundry_id: print(f'		Unable to find feature {trait_data=}')
				self.broken_links += ['cant find trait']
		return features

	def getCreatureType(self):
		cType = { "type": 'humanoid', "subtype": '' }

		for feature in self.features:
			if feature.name == 'Type':
				text = feature.raw_text.lower()
				if match := re.search(r'your creature type is (?P<type>\w+)\.', text):
					cType["type"] = match.groupdict().get('type')
				elif match := re.search(r'your creature type is both (?P<type1>\w+) and (?P<type2>\w+)\.', text):
					cType["type"] = match.groupdict().get('type1')
					cType["subtype"] = match.groupdict().get('type2').title()
				break

		return cType

	def getSpeeds(self):
		speeds = { "walk": '30' }

		for feature in self.features:
			text = feature.raw_text.lower()
			if match := re.search(r'your(?: base)? (?P<type>\w+?)(?:m?ing)? speed is (?P<number>\d+)(?: feet)?\.', text):
				speed = match.groupdict().get('type')
				number = match.groupdict().get('number')
				speeds[speed] = number
			elif match := re.search(r'you have a(?: base)? (?P<type>\w+?)(?:m?ing)? speed of (?P<number>\d+)(?: feet)?\.', text):
				speed = match.groupdict().get('type')
				number = match.groupdict().get('number')
				speeds[speed] = number
			elif match := re.search(r'you have a (?P<type>\w+?)(?:m?ing)? speed equal to your(?: base)? walk(?:ing)? speed\.', text):
				speed = match.groupdict().get('type')
				speeds[speed] = 'walk'

		return { speed: (speeds['walk'] if speeds[speed] == 'walk' else speeds[speed]) for speed in speeds }

	def getTraits(self):
		choices, grants = [], []
		for feature in self.features:
			fchoices, fgrants = feature.traits
			if fchoices: choices.extend(fchoices)
			if fgrants: grants.extend(fgrants)

		return { "choices": choices, "grants": grants }

	def getAdvancements(self, importer):
		advancements = []

		uids = [ f'Compendium.sw5e.speciesfeatures.{feature.foundry_id}' for feature in self.features if feature.foundry_id ]
		if len(uids): advancements.append( sw5e.Advancement.ItemGrant(name="Features", uids=uids, level=0, optional=True) )

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

		size_table = { full: abr for (abr, full) in utils.config.actor_sizes.items() }
		size = size_table[self.raw_size or "Medium"]
		advancements.append( sw5e.Advancement.Size(choices=[size]))

		# TODO: support non default traits
		if self.traits["choices"] or self.traits["grants"]:
			advancements.append( sw5e.Advancement.Trait(choices=self.traits["choices"], grants=self.traits["grants"]) )

		return advancements

	def getData(self, importer):
		data = super().getData(importer)[0]

		data["system"]["description"] = { "value": self.getDescription() }
		data["system"]["source"] = self.raw_contentSource
		data["system"]["identifier"] = utils.text.slugify(self.name, capitalized=False)
		data["system"]["details"] = { "isDroid": self.creature_type["type"] == 'droid' }
		data["system"]["type"] = self.creature_type
		data["system"]["speeds"] = self.speeds
		data["system"]["advancement"] = [ adv.getData(importer) for adv in self.advancements ]
		data["system"]["skinColorOptions"] = { "value": self.raw_skinColorOptions }
		data["system"]["hairColorOptions"] = { "value": self.raw_hairColorOptions }
		data["system"]["eyeColorOptions"] = { "value": self.raw_eyeColorOptions }
		data["system"]["colorScheme"] = { "value": self.raw_colorScheme }
		data["system"]["distinctions"] = { "value": self.raw_distinctions }
		data["system"]["heightAverage"] = { "value": self.raw_heightAverage }
		data["system"]["heightRollMod"] = { "value": self.raw_heightRollMod }
		data["system"]["weightAverage"] = { "value": self.raw_weightAverage }
		data["system"]["weightRollMod"] = { "value": self.raw_weightRollMod }
		data["system"]["homeworld"] = { "value": self.raw_homeworld }
		data["system"]["slanguage"] = { "value": self.raw_language }
		data["system"]["-=traits"] = None
		data["system"]["-=damage"] = None
		data["system"]["-=armorproperties"] = None
		data["system"]["-=weaponproperties"] = None

		return [data]
