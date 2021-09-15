import sw5e.Entity, utils.text
import re, json

class Power(sw5e.Entity.Item):
	def __init__(self, raw_item, old_item, uid, importer):
		super().__init__(raw_item, old_item, uid, importer)

		self.type = "power"

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

		self.activation_type, self.activation_num, self.activation_condition = self.getActivation()
		self.duration_value, self.duration_unit, self.concentration = self.getDuration()
		target_range = self.getTargetRange()
		self.target_val, self.target_unit, self.target_type = target_range['target']
		self.range_val, self.range_unit = target_range['range']
		self.uses, self.recharge = 0, ""
		self.action_type, self.ability, self.damage, self.formula, self.save = self.getAction()
		## TODO: Get action type, ability, damage, formula, save
		self.school = self.getSchool()

	def getActivation(self):
		activation_type = ('none', 'action', 'bonus', 'reaction', 'minute', 'hour')[self.castingPeriodEnum] or 'none'

		match = re.search(r'^(\d+) ', self.castingPeriodText or '')
		activation_num = int(match.group(1)) if match else 0

		match = re.search(r'reaction, which you take (.*)$', self.castingPeriodText or '')
		activation_condition = match.group(1) if match else ''

		return activation_type, activation_num, activation_condition

	def getDuration(self):
		pattern = r'(?P<inst>Instantaneous)|(?P<conc>up to )?(?P<val>\d+) (?P<unit>\w+?)s?'

		if (match := re.search(pattern, self.duration or '')):
			if match.group('inst'): return None, "", False
			else:
				match.group('val', 'unit', 'conc')
		return None, "", False

	def getTargetRange(self):
		target_range = {
			'target': (0, '', ''),
			'range': (None, '')
		}

		pattern = r'(?P<r_val>\d+) (?P<r_unit>\w+)'
		pattern += r'|(?P<self>[Ss]elf)'
		pattern += r'(?: \((?P<t_val>\d+)-(?P<t_unit>\w+)(?:-radius)? (?P<t_type>\w+)\))?'

		if (match := re.search(pattern, self.range or '')):
			if match.group('self'):
				target_range['range'] = (None, 'self')
				target_range['target'] = match.group('t_val', 't_unit', 't_type')
			else:
				range_val = match.group('r_val')
				range_unit = match.group('r_unit')
				if range_val and range_unit: target_range['range'] = (range_val, range_unit)

		return target_range

	def getAction(self):
		action_type, ability, damage, formula, save = "", "", { "parts": [], "versatile": '' }, "", ""
		description = self.description
		scale = None

		## Get default ability score
		if self.powerType == 'Tech': ability = 'int'
		elif self.forceAlignment == 'drl': ability = 'cha'
		elif self.forceAlignment == 'lgt': ability = 'wis'

		## At-Will power scaling
		pattern = r'(?:This|The) power[\'’]s(?: [^\s]+){,10} (?:when you reach 5th|at higher levels)|At 5th level'
		if (match := re.search(pattern, description)):
			description, scale = description[:match.start()], description[match.start():]
		## Leveled power upcasting
		pattern = r'Force Potency|Overcharge Tech'
		if (match := re.search(pattern, description)):
			description, scale = description[:match.start()], description[match.end():]

		#TODO: Process the power's scaling

		## Power Attack
		pattern = r'[Mm]ake a (ranged|melee) (force|tech) attack'
		if (match := re.search(pattern, description)):
			if match.group(0) == 'ranged': action_type = 'rpak'
			else: action_type = 'mpak'

		## Saving Throw
		p_ability = r'Strength|Dexterity|Constitution|Intelligence|Wisdom|Charisma'
		pattern = r'(?:must (?:first )?|can )?(?:succeed on|make|makes|if it fails) an? '
		pattern += r'(?P<save1>' + p_ability + r')(?: or (?P<save2>' + p_ability + r'))? saving throw'
		if (match := re.search(pattern, description)):
			action_type = action_type or "save"
			#TODO find a way to use save1 or save2
			save = match.group('save1')[:3].lower()

		## Dice formula
		p_formula = r'(?P<dice>\d*d\d+)?\s*\+?\s*(?P<flat>\d+)?\s*(?:\+ your (?P<castmod>tech|force)casting (?:ability )?modifier)?'

		## Healing
		#TODO: temporary hit points
		pattern = r'(?:(?:re)?gains? (?:a number of )?(?P<temp>temporary )?hit points equal to |hit points increase by )' + p_formula
		pattern2 = r'(?:(?:re)?gains?|restores?) ' + p_formula + r' (?P<temp>temporary )?hit points'
		if (match := (re.search(pattern, description) or re.search(pattern2, description))):
			action_type = action_type or "heal"

			dice, flat, castmod, temp = match.group('dice', 'flat', 'castmod', 'temp')

			if dice or flat or castmod:
				formula = dice
				if flat:
					if formula: formula = f'{formula} + {flat}'
					else: formula = flat
				if castmod:
					formula = f'{formula or ""} + @mod'
				damage["parts"].append([ formula, 'temphp' if temp else 'healing' ])
		description = re.sub(pattern, r'FORMULA', description)
		description = re.sub(pattern2, r'FORMULA', description)

		## Damage
		pattern = r'(?:(?:takes?|taking|deals?|dealing) (?:an (?:extra|additional) |up to )?|, | (?:and|plus) (?:another )?)' + p_formula + r'(?: of)?(?: (?P<type>\w+)(?:, (?:or )?\w+)*)?(?: damage|(?= [^\n]+ damage))'
		pattern2 = r'(?:[Tt]he (?P<type>\w+ )?damage (?:also )?increases by|base damage is|damage die becomes a) ' + p_formula
		def foo(match):
			nonlocal action_type
			nonlocal damage
			dice, flat, castmod = match.group('dice', 'flat', 'castmod')
			dmg_type = match.group('type') or '' if 'type' in match.groupdict() else ''

			if dice or flat or castmod:
				action_type = action_type or 'other'
				formula = dice
				if flat:
					if formula: formula = f'{formula} + {flat}'
					else: formula = flat
				if castmod:
					formula = f'{formula or ""} + @mod'
				damage["parts"].append([ formula, dmg_type ])
				return 'FORMULA'
			else:
				return match.group(0)
		description = re.sub(pattern, foo, description)
		description = re.sub(pattern2, foo, description)

		## 'Versatile' dice
		pattern = r'[Oo]therwise, it takes ' + p_formula
		if (match := re.search(pattern, description)):
			dice, flat, castmod = match.group('dice', 'flat', 'castmod')

			formula = dice
			if flat:
				if formula: formula = f'{formula} + {flat}'
				else: formula = flat
			if castmod:
				formula = f'{formula or ""} + @mod'
			damage["versatile"] = formula
		description = re.sub(pattern, r'FORMULA', description)

		## Other dice
		pattern = r'[Rr]oll (?:a )?' + p_formula
		description = re.sub(pattern, foo, description)

		## Check for unprocessed dice
		if (match := re.search(r'\d*d\d+', description)):
			## TODO: Rework this block
			match2 = re.search(r'is reduced by ' + match.group(0), description)
			if self.name in ('Alter Self', 'Spectrum Bolt'):
				pass
			elif match2 or self.name in ('Earthquake', 'Preparedness', 'Whirlwind', 'Will of the Force', 'Energetic Burst', 'Force Vision', 'Greater Feedback', 'Insanity'):
				formula = match.group(0)
			else:
				print(f'Unprocessed dice {match.group(0)} in {self.name}')
				print(f'{description=}')
				print(f'{self.description=}')
				x = exitaaa

		action_type = action_type or 'other'

		## Change the actual description to have dice rolls
		self.description = re.sub(r'(\d*d\d+\s*)x(\s*\d+)', r'\1*\2', self.description)
		self.description = re.sub(r'(\d*d\d+(?:\s*(?:\+|\*)\s*\d+)?)', r'[[/r \1]]', self.description)

		return action_type, ability, damage, formula, save

	def getSchool(self):
		if self.powerType == 'Tech': return 'tec'
		return ('', 'uni', 'drk', 'lgt')[self.forceAlignmentEnum]

	def getImg(self):
		name = self.name
		name = re.sub(r'\s', r'', name)
		name = re.sub(r'\\', r'_', name)

		return f'systems/sw5e/packs/Icons/{self.powerType}%20Powers/{name}.webp'

	def getDescription(self):
		text = self.description
		if self.prerequisite:
			text = f'_**Prerequisite**: {self.prerequisite}_\n{text}'
		return utils.text.markdownToHtml(text)

	def getData(self, importer):
		data = super().getData(importer)[0]

		data["img"] = self.getImg()

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
		data["data"]["uses"] = {}
		data["data"]["consume"] = {}

		#TODO: extract ability, damage and other rolls
		data["data"]["ability"] = self.ability
		data["data"]["actionType"] = self.action_type
		data["data"]["attackBonus"] = 0
		data["data"]["chatFlavor"] = ''
		data["data"]["critical"] = None
		data["data"]["damage"] = self.damage
		data["data"]["formula"] = ''
		data["data"]["save"] = {
			"ability": self.save,
			"dc": None,
			"scaling": "power"
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
