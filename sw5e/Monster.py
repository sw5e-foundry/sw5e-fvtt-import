import sw5e.Entity, utils.text, utils.config
import re, json

class MonsterBehavior(sw5e.Entity.Entity):
	def load(self, raw_item):
		super().load(raw_item)

		attrs = [
			"monsterBehaviorTypeEnum",
			"monsterBehaviorType",
			"description",
			"descriptionWithLinks",
			"attackTypeEnum",
			"attackType",
			"restrictions",
			"attackBonus",
			"range",
			"numberOfTargets",
			"damage",
			"damageRoll",
			"damageTypeEnum",
			"damageType",

			"contentTypeEnum",
			"contentType",
			"contentSourceEnum",
			"contentSource",
			"partitionKey",
			"rowKey",
			"timestamp",

			"source",
			"sourceName",
			"sourceImg",
			"sourceProf",
			"sourceAbil",
		]
		for attr in attrs: setattr(self, f'raw_{attr}', utils.text.clean(raw_item, attr))

		self.type = self.loadType()
		self.description = self.loadDescription()
		self.activation, self.recharge, self.uses = self.loadActivation()
		self.range = self.loadRange()
		self.target = self.loadTarget()
		self.duration = self.loadDuration()
		self.actionType, self.damage, self.formula, self.save, self.attackBonus = self.loadAction()
		self.source = self.raw_contentSource

	def loadType(self):
		return "feat" if self.raw_attackType == "None" else "weapon"

	def loadDescription(self):
		description = self.raw_description
		description = utils.text.markdownToHtml(description)
		if self.type == "weapon": description = f'<section class="secret">\n{description}\n</section>'
		return { "value": description}

	def loadActivation(self):
		activation, recharge, uses = None, None, None
		restrictions = self.raw_restrictions or ''

		if self.raw_monsterBehaviorType != 'Trait':
			activation = {
				"type": self.raw_monsterBehaviorType.lower(),
				"cost": 1
			}
			if match := re.search(r'costs (?P<cost>\d+) actions?', restrictions.lower()):
				activation["cost"] = match["cost"]
				restrictions = restrictions[:match.start()] + restrictions[match.end():]
			if match := re.search(r'recharge (?:(?P<rec>\d+)-)?6', restrictions.lower()):
				recharge = {
					"value": int(match["rec"] or 6),
					"charged": True
				}
				restrictions = restrictions[:match.start()] + restrictions[match.end():]
			if match := re.search(r'(?P<uses>\d+)/(?P<period>\w+)', restrictions.lower()):
				uses = {
					"max": int(match["uses"]),
					"per": match["period"]
				}
				restrictions = restrictions[:match.start()] + restrictions[match.end():]
			if match := re.search(r'recharges after a (?P<short>short or )?long rest', restrictions.lower()):
				uses = {
					"max": 1,
					"per": 'sr' if match["short"] else 'lr'
				}
				restrictions = restrictions[:match.start()] + restrictions[match.end():]
			restrictions = restrictions.strip()
			if restrictions: activation["condition"] = restrictions

		return activation, recharge, uses

	def loadRange(self):
		if match := re.search(r'(?:range|reach) (?P<value>\d+)(?:/(?P<long>\d+))? (?P<units>\w+)', (self.raw_range or '').lower()):
			return match.groupdict()

		return None

	def loadTarget(self):
		if self.raw_attackType == "None":
			target, units, value = utils.text.getTarget(self.raw_description, self.name)
			return {
				"type": target,
				"units": units,
				"value": value
			}
		else:
			target, value = None, None

			target_text = (self.raw_numberOfTargets or '').lower()
			if match := re.search(r'(one)?(two)?(three)?(four)?(five)?(six)?(seven)?(eight)?(nine)?(ten)?(?P<digits>\d+)?', target_text):
				if match["digits"]: value = match["digits"]
				else:
					for i in range(1, 11):
						if match[i]: value = i

			if match := re.search(r'creature|droid|ally|enemy|object|starship', target_text):
				target = match[0]

			return {
				"type": target,
				"value": value
			}

	def loadDuration(self):
		value, units = utils.text.getDuration(self.raw_description, self.name)
		return {
			"value": value,
			"units": units
		}

	def loadAction(self):
		action_type, damage, other_formula, save, to_hit = None, None, None, None, None
		if self.activation:
			if self.raw_attackType == "None":
				action_type, damage, other_formula, save_ability, save_dc, _ = utils.text.getAction(self.raw_description, self.name)
				if save_ability and save_dc:
					save = {
						"ability": save_ability,
						"dc": save_dc,
						"scaling": "flat",
					}
			else:
				action_type = ('other', 'mwak', 'rwak')[self.raw_attackTypeEnum]
				damage = {
					"parts": [[ self.raw_damageRoll, (self.raw_damageType or 'none').lower() ]]
				} if self.raw_damageRoll else None

				attr = "dex" if action_type == "rwak" else "str"
				attrVal = self.raw_sourceAbil[attr]["value"]
				attrMod = (attrVal // 2) - 5

				to_hit = (self.raw_attackBonus or 0) - (attrMod + self.raw_sourceProf)
		return action_type, damage, other_formula, save, to_hit



	def process(self, importer):
		super().process(importer)

		self.processID()

	def processID(self):
		if not self.foundry_id: self.foundry_id = utils.text.randomID()



	def getImg(self):
		return self.raw_sourceImg

	def getData(self, importer):
		data = super().getData(importer)[0]

		data["_id"] = self.foundry_id
		data["type"] = self.type
		data["img"] = self.getImg()
		data["data"] = {}

		for attr in ('description', 'activation', 'recharge', 'uses', 'range', 'target', 'duration', 'actionType', 'damage', 'formula', 'save', 'attackBonus', 'source'):
			if val := getattr(self, attr): data["data"][attr] = val

		if self.type == 'weapon':
			data["data"]["weaponType"] = 'natural'
			data["data"]["equipped"] = True
			data["data"]["proficient"] = True

		return [data]

class Monster(sw5e.Entity.Actor):
	def load(self, raw_item):
		super().load(raw_item)

		attrs = [
			"flavorText",
			"sectionText",
			"sizeEnum",
			"size",
			"types",
			"alignment",
			"armorClass",
			"armorType",
			"hitPoints",
			"hitPointRoll",
			"speed",
			"speeds",
			"strength",
			"strengthModifier",
			"dexterity",
			"dexterityModifier",
			"constitution",
			"constitutionModifier",
			"intelligence",
			"intelligenceModifier",
			"wisdom",
			"wisdomModifier",
			"charisma",
			"charismaModifier",
			"savingThrows",
			"skills",
			"damageImmunities",
			"damageImmunitiesOther",
			"damageResistances",
			"damageResistancesOther",
			"damageVulnerabilities",
			"damageVulnerabilitiesOther",
			"conditionImmunities",
			"conditionImmunitiesOther",
			"senses",
			"languages",
			"challengeRating",
			"experiencePoints",
			"behaviors",
			"imageUrls",
			"contentTypeEnum",
			"contentType",
			"contentSourceEnum",
			"contentSource",
			"partitionKey",
			"rowKey",
			"timestamp",
			"eTag",
		]
		for attr in attrs: setattr(self, f'raw_{attr}', utils.text.clean(raw_item, attr))

		self.biography = self.loadBiography()
		self.creature_type = self.loadType()
		self.cr = self.loadChallengeRating()
		self.proficiency_bonus = self.loadProficiencyBonus()
		self.ac = self.loadArmorClass()
		self.senses = self.loadSenses()
		self.abilities = self.loadAbilities()
		self.skills = self.loadSkills()
		self.size = self.loadSize()
		self.ci = self.loadConditionImmunities()
		self.di = self.loadDamageImmunities()
		self.dr = self.loadDamageResistances()
		self.dv = self.loadDamageVulnerabilities()
		self.languages = self.loadLanguages()
		self.items = self.loadBehaviors()

	def loadBiography(self):
		return utils.text.markdownToHtml(f'{self.raw_sectionText}\n{self.raw_flavorText}')

	def loadType(self):
		# TODO: recognize non-custom types
		return {
			"value": 'custom',
			"custom": self.raw_types[0]
		}

	def loadChallengeRating(self):
		cr = self.raw_challengeRating
		if type(cr) == int: return cr
		parts = cr.split('/')
		return int(parts[0]) / int(parts[1])

	def loadProficiencyBonus(self):
		return (self.cr + 7) // 4

	def loadArmorClass(self):
		# TODO: recognize non-custom ac
		return {
			"calc": 'natural' if self.raw_armorType == 'natural armor' else 'flat',
			"flat": self.raw_armorClass
		}

	def loadSenses(self):
		senses = {}
		pattern = r'(?P<sense>[\w ]+) (?P<dist>[+-]?\d+) Ft\.'
		if self.raw_senses:
			for text in self.raw_senses:
				if match := re.match(pattern, text):
					sense = match["sense"].lower()
					dist = int(match["dist"])
					senses[sense] = dist
		return senses

	def loadAbilities(self):
		abilities = {
			attr["id"]: {
				"name": attr["name"],
				"value": getattr(self, f'raw_{attr["name"].lower()}'),
				"mod": getattr(self, f'raw_{attr["name"].lower()}Modifier'),
			}
			for attr in utils.config.attributes
		}

		if self.raw_savingThrows:
			for save in self.raw_savingThrows:
				attr = save[:3].lower()
				bonus = int(save[4:])
				if attr in abilities:
					mod = abilities[attr]["mod"]
					if (bonus - mod) == 0: abilities[attr]["proficient"] = 0
					elif (bonus - mod) == (self.proficiency_bonus // 2): abilities[attr]["proficient"] = 0.5
					elif (bonus - mod) == (self.proficiency_bonus * 2): abilities[attr]["proficient"] = 2
					else: abilities[attr]["proficient"] = 1
				else: raise ValueError(save, attr, bonus)

		return abilities

	def loadSkills(self):
		mapping = {
			skl["name"].lower(): {
				"id": skl["id"],
				"attr": skl["attr"],
				"attrMod": self.abilities[skl["attr"]]["mod"]
			}
			for skl in utils.config.skills
		}

		skills = {}
		pattern = r'(?P<skill>[\w ]+) (?P<bonus>[+-]?\s*\d+)'
		if self.raw_skills:
			for text in self.raw_skills:
				if match := re.match(pattern, text):
					skill = mapping[match["skill"].lower()]
					mod = skill["attrMod"]
					bonus = int(match["bonus"])
					if (bonus - mod) == 0: skills[skill["id"]] = { "proficient": 0 }
					if (bonus - mod) == self.proficiency_bonus: skills[skill["id"]] = { "proficient": 1 }
					if (bonus - mod) < self.proficiency_bonus: skills[skill["id"]] = { "proficient": 0.5 }
					if (bonus - mod) > self.proficiency_bonus: skills[skill["id"]] = { "proficient": 2 }
		return skills

	def loadSize(self):
		sizes = [ 'tiny', 'sm', 'med', 'lg', 'huge', 'grg' ]
		return sizes[self.raw_sizeEnum-1] or 'med'

	def loadConditionImmunities(self):
		imm = [ val.lower() for val in self.raw_conditionImmunities ]
		other = self.raw_conditionImmunitiesOther or []
		if 'disease' in other:
			imm += ['diseased']
			other = [ c for c in other if c != 'disease' ]
		other = '; '.join(other)
		return imm, other

	def loadDamageImmunities(self):
		return [ val.lower() for val in self.raw_damageImmunities ]

	def loadDamageResistances(self):
		return [ val.lower() for val in self.raw_damageResistances ]

	def loadDamageVulnerabilities(self):
		return [ val.lower() for val in self.raw_damageVulnerabilities ]

	def loadLanguages(self):
		valid = [
			"abyssin",
			"aleena",
			"antarian",
			"anzellan",
			"aqualish",
			"arconese",
			"ardennian",
			"arkanian",
			"balosur",
			"barabel",
			"galactic basic",
			"besalisk",
			"binary",
			"bith",
			"bocce",
			"bothese",
			"catharese",
			"cerean",
			"chadra-fan",
			"chagri",
			"cheunh",
			"chevin",
			"chironan",
			"clawdite",
			"codruese",
			"colicoid",
			"dashadi",
			"defel",
			"devaronese",
			"dosh",
			"draethos",
			"durese",
			"dug",
			"ewokese",
			"falleen",
			"felucianese",
			"gamorrese",
			"gand",
			"geonosian",
			"givin",
			"gran",
			"gungan",
			"hapan",
			"harchese",
			"herglese",
			"honoghran",
			"huttese",
			"iktotchese",
			"ithorese",
			"jawaese",
			"kaleesh",
			"kaminoan",
			"karkaran",
			"keldor",
			"kharan",
			"killik",
			"klatooinian",
			"kubazian",
			"kushiban",
			"kyuzo",
			"lannik",
			"lasat",
			"lowickese",
			"lurmese",
			"mandoa",
			"miralukese",
			"mirialan",
			"moncal",
			"mustafarian",
			"muun",
			"nautila",
			"ortolan",
			"pakpak",
			"pyke",
			"quarrenese",
			"rakata",
			"rattataki",
			"rishii",
			"rodese",
			"ryn",
			"selkatha",
			"semblan",
			"shistavanen",
			"shyriiwook",
			"sith",
			"squibbian",
			"sriluurian",
			"ssi-ruuvi",
			"sullustese",
			"talzzi",
			"tarasinese",
			"thisspiasian",
			"togorese",
			"togruti",
			"toydarian",
			"tusken",
			"twi'leki",
			"ugnaught",
			"umbaran",
			"utapese",
			"verpine",
			"vong",
			"voss",
			"yevethan",
			"zabraki",
			"zygerrian",
		]
		languages = {
			"value": [],
			"custom": ""
		}
		for lng in self.raw_languages:
			if not lng: continue
			lng = lng.lower()
			if lng.startswith("speaks "): lng = lng[7:]
			if lng == "galactic basic":
				languages["value"].append("basic")
			elif lng in valid:
				languages["value"].append(lng)
			elif lng not in ('—', '-', 'none'):
				if languages["custom"] != "": languages["custom"] += "; "
				languages["custom"] += lng
		return languages

	def loadBehaviors(self):
		behaviors = {}
		for behavior_data in self.raw_behaviors:
			for key in ('timestamp', 'contentTypeEnum', 'contentType', 'contentSourceEnum', 'contentSource', 'partitionKey', 'rowKey'):
				behavior_data[key] = getattr(self, f'raw_{key}')
			behavior_data["source"] = 'Monster'
			behavior_data["sourceName"] = self.name
			behavior_data["sourceImg"] = self.getImg()
			behavior_data["sourceProf"] = self.proficiency_bonus
			behavior_data["sourceAbil"] = self.abilities

			uid = MonsterBehavior.getUID(behavior_data, "MonsterBehavior")
			behavior = MonsterBehavior(behavior_data, uid, None, importer_version=self.importer_version)
			behaviors[uid] = behavior

		return behaviors


	def process(self, importer):
		super().process(importer)

		self.processBehaviors(importer)

	def processBehaviors(self, importer):
		for behavior in self.items.values():
			behavior.process(importer)
			self.broken_links += behavior.broken_links


	def getImg(self, token=False, importer=None):
		#TODO: removed this after icons are fixed in the system
		return f'icons/svg/hazard.svg'
		name = utils.text.slugify(self.name);
		return f'systems/sw5e/packs/Icons/monsters/{name}/{"token" if token else "avatar"}.webp'

	def getData(self, importer):
		data = super().getData(importer)[0]

		data["type"] = 'npc'
		data["data"]["source"] = self.raw_contentSource
		data["data"]["details"] = {
			"biography": {
				"value": self.biography
			},
			"type": self.creature_type,
			"alignment": self.raw_alignment,
			"cr": self.cr,
			"source": self.raw_contentSource
		}
		data["data"]["attributes"] = {
			"ac": self.ac,
			"hp": {
				"max": self.raw_hitPoints,
				"value": self.raw_hitPoints,
				"formula": self.raw_hitPointRoll
			},
			"senses": self.senses
		}
		data["data"]["abilities"] = self.abilities
		data["data"]["skills"] = self.skills
		data["data"]["traits"] = {
			"size": self.size,
			"ci": { "value": self.ci[0], "custom": self.ci[1] },
			"di": { "value": self.di },
			"dr": { "value": self.dr },
			"dv": { "value": self.dv },
			"languages": self.languages
		}

		data["token"] = { "img": self.getImg(token=True) }

		data["items"] = [ behavior.getData(importer)[0] for behavior in self.items.values() ]

		return [data]
