import sw5e.Entity, sw5e.templates, utils.text
import re, json

class Power(
	sw5e.Entity.Item,
	sw5e.templates.ItemDescription,
	sw5e.templates.Activities,
):
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

	def load(self, raw_entity):
		super().load(raw_entity)

		self.activation_type, self.activation_num, self.activation_condition = self.getActivation()
		self.duration_value, self.duration_unit, self.concentration = self.getDuration()
		target_range = self.getTargetRange()
		self.target_val, self.target_unit, self.target_type = target_range["target"]
		self.range_val, self.range_unit = target_range["range"]
		self.uses, self.recharge = None, None
		self.action_type, self.damage, self.formula, self.save, self.save_dc, self.scaling = self.getAction()

		self.school = self.getSchool()
		self.consume = self.getConsume()

	def process(self, importer):
		super().process(importer)

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

	def getConsume(self):
		if self.raw_level == 0: return None
		return {
			"scaling": {
				"allowed": False,
				"max": None,
			},
			"spellSlot": False,
			"targets": [
				{
					"scaling": {
						"formula": '',
						"mode": 'amount',
					},
					"target": f'powercasting.{"tech" if self.school == "tec" else "force"}.points.value',
					"type": 'attribute',
					"value": self.raw_level + 1,
				},
			],
		}

	def getImg(self, importer=None):
		name = utils.text.slugify(self.name)
		return f'modules/sw5e/icons/packs/{self.raw_powerType}%20Powers/{name}.webp'

	def getData(self, importer):
		data = super().getData(importer)[0]

		# templates.Activities
		# templates.ItemDescription

		data["system"]["ability"] = None
		data["system"]["activation"] = {
			"type": self.activation_type,
			"cost": self.activation_num,
			"condition": self.activation_condition
		}
		data["system"]["duration"] = {
			"value": self.duration_value,
			"units": self.duration_unit
		}
		data["system"]["level"] = self.raw_level
		data["system"]["materials"] = {}
		data["system"]["preparation"] = {}
		data["system"]["properties"] = [ "concentration"] if bool(self.concentration) else []
		data["system"]["range"] = {
			"value": self.range_val,
			"long": None,
			"units": self.range_unit
		}
		data["system"]["school"] = self.school
		data["system"]["sourceClass"] = None
		data["system"]["target"] = {
			"value": self.target_val,
			"width": None,
			"units": self.target_unit,
			"type": self.target_type
		}

		return [data]

	def getFile(self, importer):
		return f'{self.raw_powerType}Power'

	def getType(self):
		return 'spell'



	############################
	#    Template Functions    #
	############################

	# templates.Activities
	def getActivitiesData(self):
		return {}
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
				# "override": False,
				# "special": None,
				"units": self.range_unit or 'ft',
				"value": self.range_val,
			},
			"target": {
				"affects": {
					# "choice": False,
					# "count": "",
					# "special": "",
					# "type": "",
				},
				"template": {
					# "contiguous": False
					# "count": "",
					# "height": None,
					"size": self.target_val,
					"type": self.target_type,
					"units": self.target_unit,
					"width": None,
				},
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
			"roll": { "formula": self.formula },
		}

	# templates.ItemDescription
	def getDescription(self):
		text = self.raw_description
		if self.raw_prerequisite:
			text = f'_**Prerequisite**: {self.raw_prerequisite}_\n{text}'
		return utils.text.markdownToHtml(text)


#