import sw5e.Entity, sw5e.templates, utils.text, utils.config
import re, json

class BaseFeature(
	sw5e.Entity.Item,
	# sw5e.templates.Activities,
):
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

	def loadTraits(self):
		return utils.text.getTraits(self.raw_text.lower(), self.name)



	def process(self, importer):
		super().process(importer)

		self.duration_value, self.duration_unit = self.getDuration()
		self.target_val, self.target_unit, self.target_type = self.getTarget()
		self.range = self.getRange()
		self.uses, self.recharge = self.getUses()
		self.action_type, self.damage, self.formula, self.save, self.save_dc, _ = self.getAction()
		self.activation = self.getActivation()
		self.description = self.getDescription(importer)
		self.featType, self.featSubtype = self.getFeatType()

	def getActivation(self):
		return utils.text.getActivation(self.raw_text, self.uses, self.recharge)

	def getDuration(self):
		return utils.text.getDuration(self.raw_text, self.name)

	def getTarget(self):
		return utils.text.getTarget(self.raw_text, self.name)

	def getRange(self):
		value, unit = utils.text.getRange(self.raw_text, self.name)
		return {
			'value': value,
			'unit': unit
		}

	def getUses(self):
		return utils.text.getUses(self.raw_text, self.name)

	def getAction(self):
		return utils.text.getAction(self.raw_text, self.name)

	def getFeatType(self):
		raise NotImplementedError

	def getDescription(self, importer):
		return utils.text.markdownToHtml(self.raw_text)

	def getImg(self, importer=None):
		raise NotImplementedError

	def getActivitiesData(self):
		return {}
		return {
			"action_type": self.action_type,

			# "name": "",
			"activation": {
				"type": self.activation,
				"cost": 1 if self.activation else None
			},
			# "consumption": {},
			"description": { "value": self.description },
			"duration": {
				"value": self.duration_value,
				"units": self.duration_unit
			},
			# "effects": {},
			"range": self.range,
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
				"classification": "spell",
				"flat": False,
				"type": "melee",
			},
			"check": {
				"ability": "",
				"associated": [],
				"dc": {
					"calculation": "",
					"formula": "",
				}
			},
			"damage": {
				"critical": { "allow": True },
				"parts": self.damage["parts"],
			},
			"versatile": self.damage["versatile"],
			"effects": {},
			"enchant": {},
			"healing": self.damage["parts"],
			"save": {
				"ability": self.save,
				"dc": {
					"calculation": "" if self.save_dc else "spell",
					"formula": self.save_dc or ""
				}
			},
			"roll": self.formula,
		}

	def getData(self, importer):
		data = super().getData(importer)[0]

		data["system"]["description"] = { "value": self.description }
		# data["system"]["enchant"] = {}
		# data["system"]["identifier"] = ?
		# data["system"]["prerequisites"] = { "level": ? }
		# data["system"]["properties"] = []
		data["system"]["requirements"] = self.raw_requirements
		data["system"]["source"] = { "custom": self.raw_contentSource }
		if self.getType() == 'feat': data["system"]["type"] = {
			"value": self.featType or "",
			"subtype": self.featSubtype or ""
		}
		data["system"]["uses"] = {
			"value": None,
			"max": self.uses,
			"per": self.recharge
		}

		return [data]

class Feature(BaseFeature):
	def getAttrs(self):
		return super().getAttrs() + [ "level", "sourceEnum", "source", "sourceName", "metadata", "subtypeOverride" ]

	def load(self, raw_item):
		super().load(raw_item)

		self.subFeatures = self.getSubfeatures()

	def process(self, importer):
		self.class_name = self.getClassName(importer)

		super().process(importer)

		self.raw_requirements = self.getRequirements(importer)
		self.raw_contentType, self.raw_contentTypeEnum = self.getContentType(importer)
		self.raw_contentSource, self.raw_contentSourceEnum = self.getContentSource(importer)
		self.processSubfeatures(importer)
		self.description = self.getDescription(importer, processing=True)

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
			}.get(self.activation, 'Passive')
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

	def getRequirements(self, importer):
		req = self.raw_sourceName

		if self.class_name and self.class_name != self.raw_sourceName: req = f'{self.class_name} ({req})'
		if self.raw_level and self.raw_level > 1: req = f'{req} {self.raw_level}'
		if self.raw_requirements: req += f', {self.raw_requirements}'

		return req

	def getFile(self, importer):
		if self.raw_source in ('ClassInvocation', 'ArchetypeInvocation'): return 'ClassInvocation'
		return f'{self.raw_source}Feature'

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

	def getSubfeatures(self):
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

	def getSourceType(self):
		if self.raw_source in ('Archetype', 'ArchetypeInvocation'): return 'Archetype'
		elif self.raw_source in ('Class', 'ClassInvocation'): return 'Class'
		elif self.raw_source in ('Species',): return 'Species'

	def getSourceItem(self, importer):
		if importer and (item := importer.get(self.getSourceType(), data={ "name": self.raw_sourceName })):
			return item
		else: self.broken_links += ['cant get source item']

	def getFeatType(self):
		if self.raw_source in ('ArchetypeInvocation', 'ClassInvocation'):
			return 'class', f'{self.class_name.lower()}Invocation'
		if self.raw_source in ('Archetype', 'Class'):
			return 'class', (self.raw_subtypeOverride or None)
		if self.raw_source == 'Species':
			return 'species', (self.raw_subtypeOverride or None)

	def getDescription(self, importer, processing=False):
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

		if processing:
			for sf in self.subFeatures:
				if "fid" in sf and "comp" in sf:
					link = f'@UUID[Compendium.sw5e.{sf["comp"].lower()}.Item.{sf["fid"]}]{{{sf["name"]}}}'
					text = re.sub(fr'#### {sf["name"]}\r?\n', f'#### {link}\n', text)

		return utils.text.markdownToHtml(text)

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

class CustomizationOption(BaseFeature):
	def getFeatType(self):
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
