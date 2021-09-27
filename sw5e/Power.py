import sw5e.Entity, utils.text
import re, json

class Power(sw5e.Entity.Item):
	def load(self, raw_item):
		super().load(raw_item)

		self.powerTypeEnum = utils.text.raw(raw_item, "powerTypeEnum")
		self.powerType = utils.text.clean(raw_item, "powerType")
		self.prerequisite = utils.text.clean(raw_item, "prerequisite")
		self.level = utils.text.raw(raw_item, "level")
		self.castingPeriodEnum = utils.text.raw(raw_item, "castingPeriodEnum")
		self.castingPeriod = utils.text.clean(raw_item, "castingPeriod")
		self.castingPeriodText = utils.text.clean(raw_item, "castingPeriodText")
		self.range = utils.text.clean(raw_item, "range")
		self.duration = utils.text.clean(raw_item, "duration")
		self.concentration = utils.text.raw(raw_item, "concentration")
		self.forceAlignmentEnum = utils.text.raw(raw_item, "forceAlignmentEnum")
		self.forceAlignment = utils.text.clean(raw_item, "forceAlignment")
		self.description = utils.text.clean(raw_item, "description")
		self.higherLevelDescription = utils.text.clean(raw_item, "higherLevelDescription")
		self.contentTypeEnum = utils.text.raw(raw_item, "contentTypeEnum")
		self.contentType = utils.text.clean(raw_item, "contentType")
		self.contentSourceEnum = utils.text.raw(raw_item, "contentSourceEnum")
		self.contentSource = utils.text.clean(raw_item, "contentSource")
		self.partitionKey = utils.text.clean(raw_item, "partitionKey")
		self.rowKey = utils.text.clean(raw_item, "rowKey")

	def process(self, old_item, importer):
		super().process(old_item, importer)

		self.activation_type, self.activation_num, self.activation_condition = self.getActivation()
		self.duration_value, self.duration_unit, self.concentration = self.getDuration()
		target_range = self.getTargetRange()
		self.target_val, self.target_unit, self.target_type = target_range["target"]
		self.range_val, self.range_unit = target_range["range"]
		self.uses, self.recharge = None, ''
		self.action_type, self.damage, self.formula, self.save, self.save_dc, self.ability = self.getAction()

		self.school = self.getSchool()

	def getActivation(self):
		activation_type = ('none', 'action', 'bonus', 'reaction', 'minute', 'hour')[self.castingPeriodEnum] or 'none'

		match = re.search(r'^(\d+) ', self.castingPeriodText or '')
		activation_num = int(match[1]) if match else 0

		match = re.search(r'reaction, which you take (.*)$', self.castingPeriodText or '')
		activation_condition = match[1] if match else ''

		return activation_type, activation_num, activation_condition

	def getDuration(self):
		pattern = r'(?P<inst>Instantaneous)|(?P<perm>Permanent)|(?P<spec>Special)|(?P<conc>up to )?(?P<val>\d+) (?P<unit>turn|round|minute|hour|day|month|year)s?'

		if (match := re.search(pattern, self.duration or '')):
			if match['inst']: return None, 'inst', False
			elif match['perm']: return None, 'perm', False
			elif match['spec']: return None, 'spec', False
			else:
				return match.group('val', 'unit', 'conc')
		return None, "", False

	def getTargetRange(self):
		target_range = {
			'target': (0, '', ''),
			'range': (None, '')
		}

		if match := re.search(r'(?P<r_val>\d+) (?P<r_unit>\w+)s?|(?P<self>[Ss]elf)', self.range or ''):
			if match['self']:
				target_range['range'] = (None, 'self')
				if target := utils.text.getTarget(self.range, self.name):
					target_range['target'] = target
			else:
				units = {
					'feet': 'ft',
					'mile': 'mi',
					'miles': 'mi',
					'meter': 'm',
					'meters': 'm',
					'kilometer': 'km',
					'kilometers': 'km'
				}
				unit = units[match['r_unit']] if match['r_unit'] in units else match['r_unit']

				target_range['range'] = match['r_val'], unit

				if target := utils.text.getTarget(self.description, self.name):
					target_range['target'] = target


		return target_range

	def getAction(self):
		description, scaling = self.description, ''
		ability = ""

		## Get default ability score
		if self.powerType == 'Tech': ability = 'int'
		elif self.forceAlignment == 'drl': ability = 'cha'
		elif self.forceAlignment == 'lgt': ability = 'wis'

		## At-Will power scaling
		if match := re.search(r'(?:This|The) power[\'’]s(?: [^\s]+){,10} (?:when you reach 5th|at higher levels)|At 5th level', description):
			description, scale = description[:match.start()], description[match.start():]
		## Leveled power upcasting
		elif match := re.search(r'Force Potency|Overcharge Tech', description):
			description, scale = description[:match.start()], description[match.end():]


		#TODO: Process the power's scaling

		action_type, damage, formula, save, save_dc = utils.text.getAction(description, self.name)

		return action_type, damage, formula, save, save_dc, ability

	def getSchool(self):
		if self.powerType == 'Tech': return 'tec'
		return ('', 'uni', 'drk', 'lgt')[self.forceAlignmentEnum]

	def getImg(self):
		name = self.name
		name = re.sub(r'[/,]', r'-', name)
		name = re.sub(r'[\s]', r'', name)
		name = re.sub(r'^\(([^)]*)\)', r'\1-', name)
		name = re.sub(r'-*\(([^)]*)\)', r'-\1', name)
		return f'systems/sw5e/packs/Icons/{self.powerType}%20Powers/{name}.webp'

	def getDescription(self):
		text = self.description
		if self.prerequisite:
			text = f'_**Prerequisite**: {self.prerequisite}_\n{text}'
		return utils.text.markdownToHtml(text)

	def getData(self, importer):
		data = super().getData(importer)[0]

		data["data"]["description"] = { "value": self.getDescription() }
		data["data"]["requirements"] = self.prerequisite or ''
		data["data"]["source"] = self.contentSource
		data["data"]["activation"] = {
			"type": self.activation_type,
			"cost": self.activation_num,
			"condition": self.activation_condition
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
		data["data"]["range"] = {
			"value": self.range_val,
			"long": None,
			"units": self.range_unit
		}
		data["data"]["uses"] = {
			"value": None,
			"max": None,
			"per": ''
		}
		# data["data"]["consume"] = {}

		data["data"]["ability"] = self.ability
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

		data["data"]["level"] = self.level
		data["data"]["school"] = self.school
		data["data"]["components"] = { "concentration": bool(self.concentration) }
		data["data"]["materials"] = {}
		data["data"]["preparation"] = {}
		data["data"]["scaling"] = {
			#TODO: extract scaling
			"mode": "atwill" if self.level == 0 else "level"
		}

		return [data]

	def getFile(self, importer):
		return f'{self.powerType}Power'
