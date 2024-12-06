import sw5e.Entity, sw5e.templates, utils.text, utils.config
import re, json

class BaseFeature(
	sw5e.Entity.Item,
	sw5e.templates.Activities,
	sw5e.templates.ItemDescription,
):
	############################
	#      Load Functions      #
	############################

	def getType(self):
		return 'feat'

	def getAttrs(self):
		return super().getAttrs() + [
			"text",
			"description",
			"requirements",
			"prerequisite",
			"partitionKey",
			"rowKey",
			"contentTypeEnum",
			"contentType",
			"contentSourceEnum",
			"contentSource",
		]

	def load(self, raw_item):
		super().load(raw_item)

		self.raw_text = self.raw_text or self.raw_description
		self.raw_requirements = self.raw_requirements or self.raw_prerequisite

		self.traits = self.loadTraits()
		self.duration_value, self.duration_unit = self.loadDuration()
		self.target_val, self.target_unit, self.target_type = self.loadTarget()
		self.range_val, self.range_unit = self.loadRange()
		self.uses, self.recharge = self.loadUses()
		self.action_type, self.damage, self.formula, self.save, self.save_dc, _ = self.loadAction()
		self.activation_type, self.activation_num, self.activation_condition = self.loadActivation()
		self.featType, self.featSubtype = self.loadFeatType()
		self.consume = self.loadConsume()

	def loadTraits(self):
		return utils.text.getTraits(self.raw_text.lower(), self.name)

	def loadDuration(self):
		return utils.text.getDuration(self.raw_text, self.name)

	def loadUses(self):
		return utils.text.getUses(self.raw_text, self.name)

	def loadTarget(self):
		return utils.text.getTarget(self.raw_text, self.name)

	def loadRange(self):
		return utils.text.getRange(self.raw_text, self.name)

	def loadAction(self):
		return utils.text.getAction(self.raw_text, self.name)

	def loadConsume(self):
		return {}

	def loadActivation(self):
		return utils.text.getActivation(self.raw_text, self.uses, self.recharge), 1, None

	def loadFeatType(self):
		raise NotImplementedError

	############################
	#    Process Functions     #
	############################

	def process(self, importer):
		super().process(importer)

	############################
	#      Other Functions     #
	############################

	def getImg(self, importer=None):
		raise NotImplementedError

	def getData(self, importer):
		data = super().getData(importer)[0]

		# templates.Activities
		data["system"]["uses"] = {
			"value": None,
			"max": self.uses,
			"per": self.recharge
		}
		# templates.ItemDescription

		# data["system"]["enchant"] = {}
		if self.getType() == 'feat': data["system"]["type"] = {
			"value": self.featType or "",
			"subtype": self.featSubtype or ""
		}
		# data["system"]["prerequisites"] = { "level": ? }
		# data["system"]["properties"] = []
		data["system"]["requirements"] = self.raw_requirements

		return [data]

	############################
	#    Template Functions    #
	############################

	# templates.Activities
	def getActivitiesData(self):
		return None
	def processActivitiesData(self, importer):
		damage, healing = self.damage.splitTypes(['healing', 'temphp'])
		healing = healing.parts[0] if len(healing.parts) else None

		return {
			"action_type": self.action_type,
			# "name": "",
			"activation": {
				"type": self.activation_type,
				"cost": self.activation_num,
				"condition": self.activation_condition,
			},
			"consumption": self.consume or {},
			"description": { "value": self.description },
			"duration": {
				"value": self.duration_value,
				"units": self.duration_unit
			},
			# "effects": {},
			"range": {
				"value": self.range_val,
				"long": None,
				"units": self.range_unit or 'ft',
			},
			"target": {
				"value": self.target_val,
				"width": None,
				"units": self.target_unit,
				"type": self.target_type
			},
			# "uses": {},

			"attack": {
				"ability": "",
				"bonus": "",
				"critical": { "threshold": None },
				"flat": False,
				"type": {
					"value": 'melee',
					"classification": 'spell',
				},
			},
			"check": {
				"ability": "",
				"associated": [],
				"dc": {
					"calculation": "",
					"formula": "",
				}
			},
			"damage": damage,
			"effects": {},
			"enchant": {},
			"healing": healing,
			"save": {
				"ability": self.save,
				"dc": {
					"calculation": "" if self.save_dc else "spellcasting",
					"formula": self.save_dc or ""
				}
			},
			"roll": self.formula,
		}

	# templates.ItemDescription
	def getDescription(self):
		return utils.text.markdownToHtml(self.raw_text)
	def processDescription(self, importer):
		self.description = utils.text.markdownToHtml(self.raw_text)
	def processSource(self, importer):
		self.source = self.raw_contentSource


class Feature(
	BaseFeature
):
	############################
	#      Load Functions      #
	############################

	def getAttrs(self):
		return super().getAttrs() + [ "level", "sourceEnum", "source", "sourceName", "metadata", "subtypeOverride" ]

	def load(self, raw_item):
		super().load(raw_item)

		self.subFeatures = self.loadSubfeatures()

	def loadFeatType(self):
		if self.raw_source in ('ArchetypeInvocation', 'ClassInvocation'):
			return 'class', (self.raw_subtypeOverride or None)
		if self.raw_source in ('Archetype', 'Class'):
			return 'class', (self.raw_subtypeOverride or None)
		if self.raw_source == 'Species':
			return 'species', (self.raw_subtypeOverride or None)

	def loadSubfeatures(self):
		subFeatures = []

		for text in re.split(r'(?<!#)####(?!#)', self.raw_text)[1:]:
			lines = text.strip().split('\n')
			data = {
				"name": lines[0],
				"text": '\n'.join(lines[1:]),
				"comp": f'{self.getSourceType()}features',
			}
			subFeatures.append(data)

		return subFeatures

	############################
	#    Process Functions     #
	############################

	def process(self, importer):
		self.class_name = self.getClassName(importer)

		super().process(importer)

		self.raw_requirements = self.getRequirements(importer)
		self.raw_contentType, self.raw_contentTypeEnum = self.getContentType(importer)
		self.raw_contentSource, self.raw_contentSourceEnum = self.getContentSource(importer)
		self.processSubfeatures(importer)
		self.processFeatType(importer)

	def getRequirements(self, importer):
		req = self.raw_sourceName

		if self.class_name and self.class_name != self.raw_sourceName: req = f'{self.class_name} ({req})'
		if self.raw_level and self.raw_level > 1: req = f'{req} {self.raw_level}'
		if self.raw_requirements: req += f', {self.raw_requirements}'

		return req

	def getContentType(self, importer):
		if self.raw_contentType and self.raw_contentTypeEnum: return self.raw_contentType, self.raw_contentTypeEnum

		if sourceItem := self.getSourceItem(importer):
			return sourceItem.raw_contentType, sourceItem.raw_contentTypeEnum
		return '', 0

	def getContentSource(self, importer):
		if self.raw_contentSource and self.raw_contentSourceEnum: return self.raw_contentSource, self.raw_contentSourceEnum

		if sourceItem := self.getSourceItem(importer):
			return sourceItem.raw_contentSource, sourceItem.raw_contentSourceEnum
		return '', 0

	def processSubfeatures(self, importer):
		for feature in self.subFeatures:
			data = {
				"name": feature["name"],
				"source": self.raw_source,
				"sourceName": self.raw_sourceName,
				"level": self.raw_level
			}
			if entity := importer.get('Feature', data=data):
				feature["fid"] = entity.foundry_id
				feature["uid"] = entity.uid

	def processFeatType(self, importer):
		if self.raw_source in ('ArchetypeInvocation', 'ClassInvocation'):
			self.subtype = f'{self.class_name.lower()}Invocation'

	############################
	#      Other Functions     #
	############################

	def getImg(self, importer=None):
		if self.raw_source in ['Class', 'Archetype', 'ClassInvocation', 'ArchetypeInvocation']:

			class_abbr = { c["name"]: c["id"] for c in utils.config.classes }.get(self.class_name or self.raw_sourceName, 'BSKR')
			activation = {
				'bonus': 'Bonus',
				'action': 'Action',
				'reaction': 'Reaction',
				'special': 'Action',
				'none': 'Passive',
				None: 'Passive',
			}.get(self.activation_type, 'Passive')
			return f'modules/sw5e/icons/packs/Class%20Features/{class_abbr}{"-ARCH" if self.raw_source == "Archetype" else ""}-{activation}.webp'
		else:
			return f'modules/sw5e/icons/packs/{self.raw_source}/{utils.text.slugify(self.raw_sourceName)}.webp'

	def getClassName(self, importer):
		if self.raw_source in ('Archetype', 'ArchetypeInvocation'):
			if archetype := self.getSourceItem(importer):
				return archetype.raw_className
			else:
				self.broken_links += ['cant find class name']
		elif self.raw_source in ('Class', 'ClassInvocation'):
			return self.raw_sourceName

	def getFile(self, importer):
		if self.raw_source in ('ClassInvocation', 'ArchetypeInvocation'): return 'ClassInvocation'
		return f'{self.raw_source}Feature'

	def getSourceType(self):
		if self.raw_source in ('Archetype', 'ArchetypeInvocation'): return 'Archetype'
		elif self.raw_source in ('Class', 'ClassInvocation'): return 'Class'
		elif self.raw_source in ('Species',): return 'Species'

	def getSourceItem(self, importer):
		if importer and (item := importer.get(self.getSourceType(), data={ "name": self.raw_sourceName })):
			return item
		else: self.broken_links += ['cant get source item']

	def getSubEntities(self, importer):
		sub_items = []

		feature_types = {
			subf["name"].lower(): subf["id"]
			for feat in utils.config.feature_types
			for subf in (feat["subtypes"] if "subtypes" in feat else ())
		}
		subtype = feature_types.get(self.name.lower(), None)

		for feature in self.subFeatures:
			data = {}

			for key in (
				'timestamp',
				'contentTypeEnum',
				'contentType',
				'contentSourceEnum',
				'contentSource',
				'partitionKey',
				'rowKey',
				'source',
				'sourceEnum',
				'sourceName',
				'level',
			):
				data[key] = getattr(self, f'raw_{key}')

			data["name"] = feature["name"]
			data["text"] = feature["text"]
			if subtype: data["subtypeOverride"] = subtype

			sub_items.append((data, 'feature'))

		return sub_items

	def isValid(self):
		if self.raw_name == "Ability Score Improvement": return False
		return super().isValid()

	############################
	#    Template Functions    #
	############################

	# templates.ItemDescription
	def processDescription(self, importer):
		text = self.raw_text

		if self.raw_source in ('Class', 'Archetype'):
			if source_item := self.getSourceItem(importer):
				name = self.name
				if (plural := utils.text.getPlural(name)) in source_item.invocations: name = plural
				elif re.match(r'\w+ Superiority|Additional Maneuvers', name) and 'Maneuvers' in source_item.invocations: name = 'Maneuvers'
				if name in source_item.invocations:
					for name, invocation in source_item.invocations[name].items():
						if name.startswith('_'): continue
						if "foundry_id" in invocation:
							link = f'@UUID[Compendium.sw5e.invocations.Item.{invocation["foundry_id"]}]{{{invocation["name"]}}}'
							text = re.sub(fr'#### {invocation["name"]}\r?\n', fr'#### {link}\n', text)
						else:
							self.broken_links += ['no feature or foundry id']

		for sf in self.subFeatures:
			if "fid" in sf and "comp" in sf:
				link = f'@UUID[Compendium.sw5e.{sf["comp"].lower()}.Item.{sf["fid"]}]{{{sf["name"]}}}'
				text = re.sub(fr'#### {sf["name"]}\r?\n', f'#### {link}\n', text)

		self.description = utils.text.markdownToHtml(text)


class CustomizationOption(BaseFeature):
	def loadFeatType(self):
		subtype = self.__class__.__name__
		subtype = ''.join((subtype[0].lower(), subtype[1:]))
		return 'customizationOption', subtype

	def getImg(self, importer=None):
		return 'icons/svg/item-bag.svg'

	# @classmethod
	# def getUID(cls, raw_item):
	# 	uid = f'{cls.__name__}'

	# 	for key in ('name', 'source', 'sourceName', 'equipmentCategory', 'level', 'subtype'):
	# 		if key in raw_item:
	# 			value = raw_item[key]
	# 			if type(value) == str:
	# 				value = value.lower()
	# 				value = re.sub(r'[^\w\s-]', '', value)
	# 				value = re.sub(r'[\s-]+', '_', value).strip('-_')
	# 			uid += f'.{key}-{value}'
	# 	return uid
