import sw5e.Entity, utils.text
import re, json

class BaseFeature(sw5e.Entity.Item):
	def load(self, raw_item):
		super().load(raw_item)

		self.text = utils.text.clean(raw_item, "text") or utils.text.clean(raw_item, "description")
		self.requirements = utils.text.clean(raw_item, "requirements") or utils.text.clean(raw_item, "prerequisite")
		self.partitionKey = utils.text.clean(raw_item, "partitionKey")
		self.rowKey = utils.text.clean(raw_item, "rowKey")

		self.contentTypeEnum = utils.text.raw(raw_item, "contentTypeEnum")
		self.contentType = utils.text.clean(raw_item, "contentType")
		self.contentSourceEnum = utils.text.raw(raw_item, "contentSourceEnum")
		self.contentSource = utils.text.clean(raw_item, "contentSource")

	def process(self, old_item, importer):
		super().process(old_item, importer)

		self.duration_value, self.duration_unit = self.getDuration()
		self.target_val, self.target_unit, self.target_type = self.getTarget()
		self.range = self.getRange()
		self.uses, self.recharge = self.getUses()
		self.action_type, self.damage, self.formula, self.save, self.save_dc = self.getAction()
		self.activation = self.getActivation()
		self.description = self.getDescription(importer)

	def getActivation(self):
		return utils.text.getActivation(self.text, self.uses, self.recharge)

	def getDuration(self):
		return utils.text.getDuration(self.text, self.name)

	def getTarget(self):
		return utils.text.getTarget(self.text, self.name)

	def getRange(self):
		value, unit = utils.text.getRange(self.text, self.name)
		return {
			'value': value,
			'unit': unit
		}

	def getUses(self):
		return utils.text.getUses(self.text, self.name)

	def getAction(self):
		return utils.text.getAction(self.text, self.name)

	def getDescription(self, importer):
		text = utils.text.markdownToHtml(self.text)
		return { "value": text }

	def getImg(self, importer=None):
		raise NotImplementedError

	def getData(self, importer):
		data = super().getData(importer)[0]

		data["data"]["description"] = self.description
		data["data"]["requirements"] = self.requirements
		data["data"]["source"] = self.contentSource

		data["data"]["activation"] = {
			"type": self.activation,
			"cost": 1 if self.activation else None
		}
		data["data"]["duration"] = {
			"value": self.duration_value,
			"units": self.duration_unit
		}
		data["data"]["target"] = {
			"value": self.target_val,
			"width": None,
			"units": self.target_unit,
			"type": self.target_type
		}
		data["data"]["range"] = self.range
		data["data"]["uses"] = {
			"value": None,
			"max": self.uses,
			"per": self.recharge
		}
		# data["data"]["consume"] = {}
		# data["data"]["ability"] = ''

		data["data"]["actionType"] = self.action_type
		# data["data"]["attackBonus"] = 0
		# data["data"]["chatFlavor"] = ''
		# data["data"]["critical"] = None
		data["data"]["damage"] = self.damage
		data["data"]["formula"] = self.formula
		data["data"]["save"] = {
			"ability": self.save,
			"dc": self.save_dc,
			"scaling": "flat" if self.save_dc else "power"
		}

		# data["data"]["recharge"] = ''

		return [data]

class Feature(BaseFeature):
	def load(self, raw_item):
		super().load(raw_item)

		self.level = utils.text.raw(raw_item, "level")
		self.sourceEnum = utils.text.raw(raw_item, "sourceEnum")
		self.source = utils.text.clean(raw_item, "source")
		self.sourceName = utils.text.clean(raw_item, "sourceName")
		self.metadata = utils.text.raw(raw_item, "metadata")

	def process(self, old_item, importer):
		super().process(old_item, importer)

		self.class_name = self.getClassName(importer)
		self.requirements = self.getRequirements(importer)
		self.contentType, self.contentTypeEnum = self.getContentType(importer)
		self.contentSource, self.contentSourceEnum = self.getContentSource(importer)

	def getType(self):
		return "classfeature" if self.source in ['Class', 'Archetype', 'ClassInvocation', 'ArchetypeInvocation'] else "feat"

	def getImg(self, importer=None):
		if self.source in ['Class', 'Archetype', 'ClassInvocation', 'ArchetypeInvocation']:
			class_abbr = {
				'Berserker': 'BSKR',
				'Consular': 'CSLR',
				'Engineer': 'ENGR',
				'Fighter': 'FGTR',
				'Guardian': 'GRDN',
				'Monk': 'MNK',
				'Operative': 'OPRT',
				'Scholar': 'SCLR',
				'Scout': 'SCT',
				'Sentinel': 'SNTL',
			}.get(self.class_name or self.sourceName, 'BSKR')
			activation = {
				'bonus': 'Bonus',
				'action': 'Action',
				'reaction': 'Reaction',
				'special': 'Action',
				'none': 'Passive',
				None: 'Passive',
			}.get(self.activation, 'Passive')
			return f'systems/sw5e/packs/Icons/Class%20Features/{class_abbr}{"-ARCH" if self.source == "Archetype" else ""}-{activation}.webp'
		else:
			name = self.sourceName
			name = re.sub(r'[/,]', r'-', name)
			name = re.sub(r'[\s]', r'', name)
			name = re.sub(r'^\(([^)]*)\)', r'\1-', name)
			name = re.sub(r'-*\(([^)]*)\)', r'-\1', name)
			return f'systems/sw5e/packs/Icons/Species/{name}.webp'

	def getClassName(self, importer):
		if self.source in ('Archetype', 'ArchetypeInvocation'):
			if archetype := self.getSourceItem(importer):
				return archetype.className
			else:
				self.broken_links = True

	def getRequirements(self, importer):
		req = f'{self.class_name} ({self.sourceName})' if self.class_name else self.sourceName
		if self.level and self.level > 1: req = f'{req} {self.level}'

		if self.requirements: req += f', {self.requirements}'

		return req

	def getFile(self, importer):
		if self.source in ('ClassInvocation', 'ArchetypeInvocation'): return 'ClassInvocation'
		return f'{self.source}Feature'

	def getContentType(self, importer):
		if self.contentType and self.contentTypeEnum: return self.contentType, self.contentTypeEnum

		if sourceItem := self.getSourceItem(importer):
			return sourceItem.contentType, sourceItem.contentTypeEnum
		return '', 0

	def getContentSource(self, importer):
		if self.contentSource and self.contentSourceEnum: return self.contentSource, self.contentSourceEnum

		if sourceItem := self.getSourceItem(importer):
			return sourceItem.contentSource, sourceItem.contentSourceEnum
		return '', 0

	def getSourceItem(self, importer):
		if self.source in ('Archetype', 'ArchetypeInvocation'):
			if item := importer.get('archetype', data={ "name": self.sourceName }):
				return item
		elif self.source in ('Class', 'ClassInvocation'):
			if item := importer.get('class', data={ "name": self.sourceName }):
				return item
		elif self.source in ('Species',):
			if item := importer.get('species', data={ "name": self.sourceName }):
				return item
		self.broken_links = True

	def getDescription(self, importer):
		text = self.text

		if self.source in ('Class', 'Archetype'):
			if source_item := self.getSourceItem(importer):
				name = self.name
				if (plural := utils.text.getPlural(name)) in source_item.sub_item_features: name = plural
				elif re.match(r'\w+ Superiority|Additional Maneuvers', name) and 'Maneuvers' in source_item.sub_item_features: name = 'Maneuvers'
				if name in source_item.sub_item_features:
					for invocation in source_item.sub_item_features[name]:
						invocation_text = invocation["name"]
						data = {
							"name": invocation["name"],
							"source": f'{self.source}Invocation',
							"sourceName": source_item.name,
							"level": invocation["level"],
						}
						if (invocation_item := importer.get('feature', data=data)) and  invocation_item.foundry_id:
							invocation_text = f'@Compendium[sw5e.invocations.{invocation_item.foundry_id}]{{{invocation_text}}}'
						else:
							self.broken_links = True
						text += f'\n{invocation_text}'

		text = utils.text.markdownToHtml(text)

		return { "value": text }

	def getData(self, importer):
		data = super().getData(importer)[0]

		data["data"]["className"] = self.class_name

		return [data]

class CustomizationOption(BaseFeature):
	def getType(self):
		return 'feat'

	def getImg(self, importer=None):
		return 'icons/svg/item-bag.svg'

	def getData(self, importer):
		data = super().getData(importer)[0]
		class_name = self.__class__.__name__
		class_name = re.sub(r'([a-z])([A-Z])', r'\1 \2', class_name)
		data["name"] = f'{class_name} ({self.name})'
		return [data]

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
