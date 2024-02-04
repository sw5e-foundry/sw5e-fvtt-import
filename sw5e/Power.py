import sw5e.Entity, utils.text
import re, json

class Power(sw5e.Entity.Item):
	def getAttrs(self):
		return super().getAttrs() + [
			"powerTypeEnum",
			"powerType",
			"prerequisite",
			"level",
			"castingPeriodEnum",
			"castingPeriod",
			"castingPeriodText",
			"range",
			"duration",
			"concentration",
			"forceAlignmentEnum",
			"forceAlignment",
			"description",
			"higherLevelDescription",
			"contentTypeEnum",
			"contentType",
			"contentSourceEnum",
			"contentSource",
			"partitionKey",
			"rowKey",
		]

	def process(self, importer):
		super().process(importer)

		self.activation_type, self.activation_num, self.activation_condition = self.getActivation()
		self.duration_value, self.duration_unit, self.concentration = self.getDuration()
		target_range = self.getTargetRange()
		self.target_val, self.target_unit, self.target_type = target_range["target"]
		self.range_val, self.range_unit = target_range["range"]
		self.uses, self.recharge = None, None
		self.action_type, self.damage, self.formula, self.save, self.save_dc, self.scaling = self.getAction()

		self.school = self.getSchool()

	def getActivation(self):
		activation_type = ('none', 'action', 'bonus', 'reaction', 'minute', 'hour')[self.raw_castingPeriodEnum] or 'none'

		match = re.search(r'^(\d+) ', self.raw_castingPeriodText or '')
		activation_num = int(match[1]) if match else 0

		match = re.search(r'reaction, which you take (.*)$', self.raw_castingPeriodText or '')
		activation_condition = match[1] if match else ''

		return activation_type, activation_num, activation_condition

	def getDuration(self):
		pattern = r'(?P<inst>Instantaneous)|(?P<perm>Permanent)|(?P<spec>Special)|(?P<conc>up to )?(?P<val>\d+) (?P<unit>turn|round|minute|hour|day|month|year)s?'

		if (match := re.search(pattern, self.raw_duration or '')):
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

		raw_range = (self.raw_range or '').lower()

		special_units = {
			'self': 'self',
			'touch': 'touch',
			'your reach': 'touch',
			# 'varies': 'spec',
			'special': 'spec',
			# 'any': 'any',
		}
		if match := re.search(r'(?P<r_val>\d+) (?P<r_unit>\w+)s?', raw_range):
			units = {
				'feet': 'ft',
				'mile': 'mi',
				'miles': 'mi',
				'meter': 'm',
				'meters': 'm',
				'kilometer': 'km',
				'kilometers': 'km'
			}
			unit  = units.get(match['r_unit'], match['r_unit'])

			target_range['range'] = match['r_val'], unit

			if target := utils.text.getTarget(self.raw_description, self.name):
				target_range['target'] = target
		elif match := re.search('|'.join(special_units.keys()), raw_range):
			unit = special_units[match.group(0)]
			target_range['range'] = (None, unit)
			if target := utils.text.getTarget(self.raw_range, self.name):
				target_range['target'] = target
		elif match := re.search('|'.join(special_units.keys()), self.raw_description):
			unit = special_units[match.group(0)]
			target_range['range'] = (None, unit)
			if target := utils.text.getTarget(self.raw_description, self.name):
				target_range['target'] = target


		return target_range

	def getAction(self):
		description, scale = self.raw_description, ''

		## Leveled power upcasting
		if match := re.search(r'Force Potency|Overcharge Tech', description):
			description, scale = description[:match.start()], description[match.start():]
		## At-Will power scaling
		elif match := re.search(r'(?:This|The) power[\'’]s(?: [^\s]+){,10} (?:when you reach 5th|at higher levels)|At 5th level', description):
			description, scale = description[:match.start()], description[match.start():]

		action_type, damage, formula, save, save_dc, scaling = utils.text.getAction(description, self.name, scale=scale)

		return action_type, damage, formula, save, save_dc, scaling

	def getSchool(self):
		if self.raw_powerType == 'Tech': return 'tec'
		return ('', 'uni', 'drk', 'lgt')[self.raw_forceAlignmentEnum]

	def getImg(self, importer=None):
		name = utils.text.slugify(self.name)
		return f'systems/sw5e/packs/Icons/{self.raw_powerType}%20Powers/{name}.webp'

	def getDescription(self):
		text = self.raw_description
		if self.raw_prerequisite:
			text = f'_**Prerequisite**: {self.raw_prerequisite}_\n{text}'
		return utils.text.markdownToHtml(text)

	def getData(self, importer):
		data = super().getData(importer)[0]

		data["system"]["description"] = { "value": self.getDescription() }
		data["system"]["requirements"] = self.raw_prerequisite or ''
		data["system"]["source"] = self.raw_contentSource
		data["system"]["activation"] = {
			"type": self.activation_type,
			"cost": self.activation_num,
			"condition": self.activation_condition
		}
		data["system"]["duration"] = {
			"value": self.duration_value,
			"units": self.duration_unit
		}
		data["system"]["target"] = {
			"value": self.target_val,
			"width": None,
			"units": self.target_unit,
			"type": self.target_type
		}
		data["system"]["range"] = {
			"value": self.range_val,
			"long": None,
			"units": self.range_unit
		}
		data["system"]["uses"] = {
			"value": None,
			"max": None,
			"per": ''
		}
		# data["system"]["consume"] = {}

		data["system"]["actionType"] = self.action_type
		# data["system"]["attackBonus"] = 0
		# data["system"]["chatFlavor"] = ''
		data["system"]["critical"] = {
			"threshold": None,
			"damage": ""
		}
		data["system"]["damage"] = self.damage
		data["system"]["formula"] = self.formula
		data["system"]["save"] = {
			"ability": self.save,
			"dc": self.save_dc,
			"scaling": "flat" if self.save_dc else "power"
		}

		data["system"]["level"] = self.raw_level
		data["system"]["school"] = self.school
		data["system"]["components"] = { "concentration": bool(self.concentration) }
		data["system"]["materials"] = {}
		data["system"]["preparation"] = {}
		data["system"]["scaling"] = self.scaling

		return [data]

	def getFile(self, importer):
		return f'{self.raw_powerType}Power'
