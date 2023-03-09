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
		self.raw_duration_value, self.raw_duration_unit, self.raw_concentration = self.getDuration()
		target_range = self.getTargetRange()
		self.target_val, self.target_unit, self.target_type = target_range["target"]
		self.raw_range_val, self.raw_range_unit = target_range["range"]
		self.uses, self.recharge = None, None
		self.action_type, self.damage, self.formula, self.save, self.save_dc, self.ability, self.scaling = self.getAction()

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

		if match := re.search(r'(?P<r_val>\d+) (?P<r_unit>\w+)s?|(?P<self>[Ss]elf)', self.raw_range or ''):
			if match['self']:
				target_range['range'] = (None, 'self')
				if target := utils.text.getTarget(self.raw_range, self.name):
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

				if target := utils.text.getTarget(self.raw_description, self.name):
					target_range['target'] = target


		return target_range

	def getAction(self):
		description, scale = self.raw_description, ''
		ability = ""

		## Get default ability score
		if self.raw_powerType == 'Tech': ability = 'int'
		elif self.raw_forceAlignment == 'drl': ability = 'cha'
		elif self.raw_forceAlignment == 'lgt': ability = 'wis'

		## Leveled power upcasting
		if match := re.search(r'Force Potency|Overcharge Tech', description):
			description, scale = description[:match.start()], description[match.start():]
		## At-Will power scaling
		elif match := re.search(r'(?:This|The) power[\'’]s(?: [^\s]+){,10} (?:when you reach 5th|at higher levels)|At 5th level', description):
			description, scale = description[:match.start()], description[match.start():]

		action_type, damage, formula, save, save_dc, scaling = utils.text.getAction(description, self.name, scale=scale)

		return action_type, damage, formula, save, save_dc, ability, scaling

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

		data["data"]["description"] = { "value": self.getDescription() }
		data["data"]["requirements"] = self.raw_prerequisite or ''
		data["data"]["source"] = self.raw_contentSource
		data["data"]["activation"] = {
			"type": self.activation_type,
			"cost": self.activation_num,
			"condition": self.activation_condition
		}
		data["data"]["duration"] = {
			"value": self.raw_duration_value,
			"units": self.raw_duration_unit
		}
		data["data"]["target"] = {
			"value": self.target_val,
			"width": None,
			"units": self.target_unit,
			"type": self.target_type
		}
		data["data"]["range"] = {
			"value": self.raw_range_val,
			"long": None,
			"units": self.raw_range_unit
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
		data["data"]["critical"] = {
			"threshold": None,
			"damage": ""
		}
		data["data"]["damage"] = self.damage
		data["data"]["formula"] = self.formula
		data["data"]["save"] = {
			"ability": self.save,
			"dc": self.save_dc,
			"scaling": "flat" if self.save_dc else "power"
		}

		data["data"]["level"] = self.raw_level
		data["data"]["school"] = self.school
		data["data"]["components"] = { "concentration": bool(self.raw_concentration) }
		data["data"]["materials"] = {}
		data["data"]["preparation"] = {}
		data["data"]["scaling"] = self.scaling

		return [data]

	def getFile(self, importer):
		return f'{self.raw_powerType}Power'
