import sw5e.Entity, utils.text
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
		for attr in attrs: setattr(self, f'_{attr}', utils.text.clean(raw_item, attr))

	def process(self, old_item, importer):
		super().process(old_item, importer)

		self.id = self.getID(importer)
		self.type = self.getType(importer)
		self.description = self.getDescription(importer)
		self.activation, self.recharge, self.uses = self.processRestrictions(importer)
		self.range = self.getRange(importer)
		self.target = self.getTarget(importer)
		self.duration = self.getDuration(importer)
		self.actionType, self.damage, self.formula, self.save, self.attackBonus = self.getAction(importer)
		self.source = self._contentSource

	def getID(self, importer):
		if not self.foundry_id: self.broken_links = True
		return self.foundry_id or utils.text.randomID()

	def getType(self, importer):
		return "feat" if self._attackType == "None" else "weapon"

	def getDescription(self, importer):
		description = self._description
		description = utils.text.markdownToHtml(description)
		if self.type == "weapon": description = f'<section class="secret">\n{description}\n</section>'
		return { "value": description}

	def processRestrictions(self, importer):
		activation, recharge, uses = None, None, None
		restrictions = self._restrictions or ''

		if self._monsterBehaviorType != 'Trait':
			activation = {
				"type": self._monsterBehaviorType.lower(),
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

	def getRange(self, importer):
		if match := re.search(r'(?:range|reach) (?P<value>\d+)(?:/(?P<long>\d+))? (?P<units>\w+)', (self._range or '').lower()):
			return match.groupdict()

		return None

	def getTarget(self, importer):
		if self._attackType == "None":
			target, units, value = utils.text.getTarget(self._description, self.name)
			return {
				"type": target,
				"units": units,
				"value": value
			}
		else:
			target, value = None, None

			target_text = (self._numberOfTargets or '').lower()
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

	def getDuration(self, importer):
		value, units = utils.text.getDuration(self._description, self.name)
		return {
			"value": value,
			"units": units
		}

	def getAction(self, importer):
		action_type, damage, other_formula, save, to_hit = None, None, None, None, None
		if self.activation:
			if self._attackType == "None":
				action_type, damage, other_formula, save_ability, save_dc, _ = utils.text.getAction(self._description, self.name)
				if save_ability and save_dc:
					save = {
						"ability": save_ability,
						"dc": save_dc,
						"scaling": "flat",
					}
			else:
				action_type = ('other', 'mwak', 'rwak')[self._attackTypeEnum]
				damage = {
					"parts": [[ self._damageRoll, (self._damageType or 'none').lower() ]]
				} if self._damageRoll else None

				attr = "dex" if action_type == "rwak" else "str"
				attrVal = self._sourceAbil[attr]["value"]
				attrMod = (attrVal // 2) - 5

				to_hit = (self._attackBonus or 0) - (attrMod + self._sourceProf)
		return action_type, damage, other_formula, save, to_hit

	def getImg(self, importer):
		return self._sourceImg

	def getData(self, importer):
		data = super().getData(importer)[0]

		data["_id"] = self.id
		data["type"] = self.type
		data["img"] = self.getImg(importer)
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
		for attr in attrs: setattr(self, f'_{attr}', utils.text.clean(raw_item, attr))

	def process(self, old_actor, importer):
		super().process(old_actor, importer)

		self.challenge_rating = self.getChallengeRating()
		self.proficiency_bonus = self.getProficiencyBonus()
		self.creature_type = self.getType()
		self.ac = self.getArmorClass()
		self.abilities = self.getAbilities()
		self.skills = self.getSkills()
		self.senses = self.getSenses()
		self.ci = self.getConditionImmunities()
		self.processBehaviors(old_actor, importer)

	def processBehaviors(self, old_actor, importer):
		for behavior_data in self._behaviors:
			for key in ('timestamp', 'contentTypeEnum', 'contentType', 'contentSourceEnum', 'contentSource', 'partitionKey', 'rowKey'):
				behavior_data[key] = getattr(self, f'_{key}')
			behavior_data["source"] = 'Monster'
			behavior_data["sourceName"] = self.name
			behavior_data["sourceImg"] = self.getImg()
			behavior_data["sourceProf"] = self.proficiency_bonus
			behavior_data["sourceAbil"] = self.abilities

			uid = MonsterBehavior.getUID(behavior_data)
			if (not old_actor) or (old_actor.timestamp != behavior_data["timestamp"]) or (old_actor.importer_version != importer.version) or (old_actor.broken_links):
				old_item = old_actor.items.get(uid, None) if old_actor else None
				new_item = MonsterBehavior(behavior_data, old_item, uid, importer)
				self.items[uid] = new_item
				if new_item.broken_links: self.broken_links = True

	def getImg(self, token=False, importer=None):
		#TODO: removed this after icons are fixed in the system
		return f'icons/svg/hazard.svg'
		name = utils.text.slugify(self.name);
		return f'systems/sw5e/packs/Icons/monsters/{name}/{"token" if token else "avatar"}.webp'

	def getChallengeRating(self):
		cr = self._challengeRating
		if type(cr) == int: return cr
		parts = cr.split('/')
		return int(parts[0]) / int(parts[1])

	def getProficiencyBonus(self):
		return (self.challenge_rating + 7) // 4

	def getType(self):
		# TODO: recognize non-custom types
		return {
			"value": 'custom',
			"custom": self._types[0]
		}

	def getArmorClass(self):
		# TODO: recognize non-custom ac
		return {
			"calc": 'natural' if self._armorType == 'natural armor' else 'flat',
			"flat": self._armorClass
		}

	def getAbilities(self):
		mapping = {
			"str": 'strength',
			"dex": 'dexterity',
			"con": 'constitution',
			"int": 'intelligence',
			"wis": 'wisdom',
			"cha": 'charisma'
		}
		abilities = { attr: { "value": getattr(self, f'_{mapping[attr]}') } for attr in mapping }
		if self._savingThrows:
			for save in self._savingThrows:
				attr = save[:3].lower()
				if attr in mapping:
					mod = getattr(self, f'_{mapping[attr]}Modifier')
					bonus = int(save[4:])
					if (bonus - mod) == 0: abilities[attr]["proficient"] = 0
					elif (bonus - mod) == (self.proficiency_bonus // 2): abilities[attr]["proficient"] = 0.5
					elif (bonus - mod) == (self.proficiency_bonus * 2): abilities[attr]["proficient"] = 2
					else: abilities[attr]["proficient"] = 1
		return abilities

	def getSkills(self):
		mapping = {
			"acrobatics": {
				"abbr": 'acr',
				"attr": 'dexterity'
			},
			"animal handling": {
				"abbr": 'ani',
				"attr": 'wisdom'
			},
			"athletics": {
				"abbr": 'ath',
				"attr": 'strength'
			},
			"deception": {
				"abbr": 'dec',
				"attr": 'charisma'
			},
			"insight": {
				"abbr": 'ins',
				"attr": 'wisdom'
			},
			"intimidation": {
				"abbr": 'itm',
				"attr": 'charisma'
			},
			"investigation": {
				"abbr": 'inv',
				"attr": 'intelligence'
			},
			"lore": {
				"abbr": 'lor',
				"attr": 'intelligence'
			},
			"medicine": {
				"abbr": 'med',
				"attr": 'wisdom'
			},
			"nature": {
				"abbr": 'nat',
				"attr": 'intelligence'
			},
			"perception": {
				"abbr": 'prc',
				"attr": 'wisdom'
			},
			"performance": {
				"abbr": 'prf',
				"attr": 'charisma'
			},
			"persuasion": {
				"abbr": 'per',
				"attr": 'charisma'
			},
			"piloting": {
				"abbr": 'pil',
				"attr": 'intelligence'
			},
			"sleight of hand": {
				"abbr": 'slt',
				"attr": 'dexterity'
			},
			"stealth": {
				"abbr": 'ste',
				"attr": 'dexterity'
			},
			"survival": {
				"abbr": 'sur',
				"attr": 'wisdom'
			},
			"technology": {
				"abbr": 'tec',
				"attr": 'intelligence'
			}
		}
		skills = {}
		pattern = r'(?P<skill>[\w ]+) (?P<bonus>[+-]?\s*\d+)'
		if self._skills:
			for text in self._skills:
				if match := re.match(pattern, text):
					skill = mapping[match["skill"].lower()]
					mod = getattr(self, f'_{skill["attr"]}Modifier')
					bonus = int(match["bonus"])
					if (bonus - mod) == 0: skills[skill["abbr"]] = { "proficient": 0 }
					if (bonus - mod) == self.proficiency_bonus: skills[skill["abbr"]] = { "proficient": 1 }
					if (bonus - mod) < self.proficiency_bonus: skills[skill["abbr"]] = { "proficient": 0.5 }
					if (bonus - mod) > self.proficiency_bonus: skills[skill["abbr"]] = { "proficient": 2 }
		return skills

	def getSenses(self):
		senses = {}
		pattern = r'(?P<sense>[\w ]+) (?P<dist>[+-]?\d+) Ft\.'
		if self._senses:
			for text in self._senses:
				if match := re.match(pattern, text):
					sense = match["sense"].lower()
					dist = int(match["dist"])
					senses[sense] = dist
		return senses

	def getDamageImmunities(self):
		return [ val.lower() for val in self._damageImmunities ]

	def getSize(self):
		sizes = [ 'tiny', 'sm', 'med', 'lg', 'huge', 'grg' ]
		return sizes[self._sizeEnum-1] or 'med'

	def getBiography(self):
		return utils.text.markdownToHtml(f'{self._sectionText}\n{self._flavorText}')

	def getDamageResistances(self):
		return [ val.lower() for val in self._damageResistances ]

	def getDamageVulnerabilities(self):
		return [ val.lower() for val in self._damageVulnerabilities ]

	def getConditionImmunities(self):
		imm = [ val.lower() for val in self._conditionImmunities ]
		other = self._conditionImmunitiesOther or []
		if 'disease' in other:
			imm += ['diseased']
			other = [ c for c in other if c != 'disease' ]
		other = '; '.join(other)
		return imm, other

	def getLanguages(self):
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
		for lng in self._languages:
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

	def getBehaviors(self, importer):
		return [ behavior.getData(importer)[0] for behavior in self.items.values() ]

	def getData(self, importer):
		data = super().getData(importer)[0]

		data["type"] = 'npc'
		data["data"]["source"] = self._contentSource
		data["data"]["details"] = {
			"biography": {
				"value": self.getBiography()
			},
			"type": self.creature_type,
			"alignment": self._alignment,
			"cr": self._challengeRating,
			"source": self._contentSource
		}
		data["data"]["attributes"] = {
			"ac": self.ac,
			"hp": {
				"max": self._hitPoints,
				"value": self._hitPoints,
				"formula": self._hitPointRoll
			},
			"senses": self.senses
		}
		data["data"]["abilities"] = self.abilities
		data["data"]["skills"] = self.skills
		data["data"]["traits"] = {
			"size": self.getSize(),
			"ci": { "value": self.ci[0], "custom": self.ci[1] },
			"di": { "value": self.getDamageImmunities() },
			"dr": { "value": self.getDamageResistances() },
			"dv": { "value": self.getDamageVulnerabilities() },
			"languages": self.getLanguages()
		}

		data["token"] = { "img": self.getImg(token=True) }

		data["items"] = self.getBehaviors(importer)

		return [data]
