import re, json

def ncapt(patt): return f'(?:{patt})'
def capt(patt, name=None): return f'(?P<{name}>{patt})' if name else f'({patt})'


def cleanStr(string):
	if string:
		string = ' '.join(string.split(' ')) or ''
		string = re.sub(r'\ufffd', r'—', string) or ''
		string = re.sub(r'(\\+r|\\*\r)+', r'', string) or ''
		string = re.sub(r'(\\+n|\\*\n)+', r'\n', string) or ''
		return string

def markdownToHtml(lines):
	if lines:
		if type(lines) == str: lines = lines.split('\n')
		lines = list(filter(None, lines))

		inList = False
		for i in range(len(lines)):
			lines[i] = cleanStr(lines[i])

			if lines[i].startswith(r'- '):
				lines[i] = f'<li>{lines[i][2:]}</li>'

				if not inList:
					lines[i] = f'<ul>\n{lines[i]}'
					inList = True
			else:
				if lines[i].startswith(r'#'):
					count = lines[i].find(' ')
					lines[i] = f'<h{count-1}>{lines[i][count+1:]}</h{count-1}>'
				elif not lines[i].startswith(r'<'):
					lines[i] = f'<p>{lines[i]}</p>'

				if inList:
					lines[i] = f'</ul>\n{lines[i]}'
					inList = False

			lines[i] = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', lines[i])
			lines[i] = re.sub(r'\*(.*?)\*', r'<em>\1</em>', lines[i])
			lines[i] = re.sub(r'_(.*?)_', r'<em>\1</em>', lines[i])
		return '\n'.join(lines)

def getActivation(text, uses, recharge):
	if text:
		text = text.lower()

		if re.search(r'bonus action', text):
			return 'bonus'
		elif re.search(r'as an action|can take an action|you can use your action', text):
			return 'action'
		elif re.search(r'you can use your reaction|using your reaction|you can use this special reaction', text):
			return 'reaction'
		elif uses or (recharge and recharge != 'none'):
			return 'special'
	return 'none'

def getUses(text, name):
	uses, recharge = 0, 'none'

	found = False

	if text:
		text = text.lower()

		patSR = r'(finish|finishes|complete) a short(?: rest)?(?: or(?: a)? long rest)'
		patSR += r'|regain all expended uses on a short(?: or long)? rest'
		patLR = r'(finish|finishes|complete) a long rest'
		patSR += r'|regain all expended uses on a long rest'
		patRC = r'until you move 0 feet on one of your turns'
		patRC += r'|until you store'

		if re.search(patSR, text): recharge = 'sr'
		elif re.search(patLR, text): recharge = 'lr'
		elif re.search(patRC, text): recharge = 'charges'

		if not found: ## BASE +/* ABILITY modifier times, min of MIN
			pattern = r'a (?:combined |maximum )?number of (?:power surges |(?P<times>times?) )?equal to (?:(?P<base>\d+) \+ )?(?P<half>half )?your '
			pattern += r'(?P<ability1>strength|dexterity|constitution|intelligence|wisdom|charisma|critical analysis)'
			pattern += r'(?: or (?P<ability2>strength|dexterity|constitution|intelligence|wisdom|charisma))? modifier'
			pattern += r'(?: \((?:your choice, )?(?:rounded (?P<rounded>down|up) )?(?:a )?minimum of (?P<min>\d+|once)\))?'

			if match := re.search(pattern, text):
				found = True

				if match['times'] == 'time':
					print(f'		Possible typo detected on {name}, count using "time" instead of "times"')

				uses_ability1 = match['ability1'] or ''
				uses_ability2 = match['ability2'] or ''
				if uses_ability1 == 'Critical Analysis': uses_ability1 = 'int'
				else: uses_ability1 = uses_ability1[:3].lower()
				if uses_ability2: uses_ability2 = uses_ability2[:3].lower()

				uses_base = int(match['base'] or 0)
				uses_half = match['half']
				uses_rounded = match['rounded']
				uses_min = 1 if match['min'] == 'once' else int(match['min'] or 0)

				#TODO: Change this when foundry supports ability mod on max uses
				uses = f'@abilities.{uses_ability1}.score'
				if uses_ability2: uses = f'max({uses}, @abilities.{uses_ability2}.score)'
				uses = f'floor(({uses} - 10) / 2)'
				# uses = f'@abilities.{uses_ability1}.mod'
				# if uses_ability2: uses = f'max({uses}, @abilities.{uses_ability2}.mod)'

				if uses_base: uses = f'{uses_base} + {uses}'
				if uses_min: uses = f'max({uses}, {uses_min})'
				if uses_half:
					if uses_rounded == 'up':
						uses = f'ceil(({uses})/2)'
					else:
						uses = f'floor(({uses})/2)'

		if not found: ## PROF times
			pattern = r'a (?:combined )?number of times equal to (?P<half>half )?your proficiency bonus'
			pattern += r'|in excess of (?P<half2>half )?your proficiency bonus \(resetting on a long rest\)'

			if match := re.search(pattern, text):
				found = True

				uses = '@details.prof'
				if match['half'] or match['half2']:
					uses = f'floor({uses}/2)'

		sp_action = r'use (?:it|(?:this|each|the chosen) (?:feature|trait|ability))'
		sp_action += r'|initiate playing an enhanced song'
		sp_action += r'|invoke each of your totems'
		sp_action += r'|invoke a totem this way'
		sp_action += r'|create a panacea'
		sp_action += r'|manifest your ideals'
		sp_action += r'|(?:cast|do) (?:it|so)'

		sp_action_past = r'used? (?:it|(?:this|each|the chosen) (?:feature|trait|ability))'
		sp_action_past += r'|initiated? playing an enhanced song'
		sp_action_past += r'|invoked? each of your totems'
		sp_action_past += r'|invoked? a totem this way'
		sp_action_past += r'|created? a panacea'
		sp_action_past += r'|manifest(?:ed)? your ideals'
		sp_action_past += r'|(?:cast|do(?:ne)?) (?:it|so)'

		sp_n = r'one|two|three|four|five|six|seven|eight|nine|ten|\d+'
		sp_n_times = capt(sp_n) + r' times|(once|twice|thrice)'

		if not found: ## NUMBER times
			pattern = r'you can ' + ncapt(sp_action) + r' (?:a (?:combined )?total of )?' + ncapt(sp_n_times)
			pattern += r'|you have ' + capt(sp_n) + r' (?:superiority dice|amplified shots|(?:\w+ )?points)'

			if match := re.search(pattern, text):
				found = True

				number = match[1] or match[2] or match[3]
				try:
					uses = int(number)
				except ValueError:
					uses = {
						'once': 1,
						'twice': 2,
						'thrice': 3,
						'one': 1,
						'two': 2,
						'three': 3,
						'four': 4,
						'five': 5,
						'six': 6,
						'seven': 7,
						'eight': 8,
						'nine': 9,
						'ten': 10
					}[number]

		if not found: ## ONCE
			pattern = r'once you(?:[\'—]ve| have)? ' + ncapt(sp_action_past)
			pattern += r'|you (?:can[\'—]t|cannot|can not) ' + ncapt(sp_action) + r' (?:again )?until'
			pattern += r'|if you ' + ncapt(sp_action) + r' again before'

			if match := re.search(pattern, text):
				found = True

				uses = 1

		if not found: ## CUSTOM (twiceScoutLevelPlusInt)
			pattern = r'that barrier has hit points equal to twice your scout level \+ your intelligence modifier'
			if match := re.search(pattern, text):
				found = True
				uses = '2 * @classes.scout.levels + floor((@abilities.int.score - 10) / 2)'

		if not found: ## CUSTOM (twiceConsularLevelPlusWisOrCha)
			pattern = r'the barrier has hit points equal to twice your consular level \+ your wisdom or charisma modifier \(your choice\)'
			if match := re.search(pattern, text):
				found = True
				uses = '2 * @classes.consular.levels + floor((max(@abilities.wis.score, @abilities.cha.score) - 10) / 2)'

		if not found: ## CUSTOM (fiveTimesEngineerLevel)
			pattern = r'has a number of hit points equal to 5 x your engineer level'
			if match := re.search(pattern, text):
				found = True
				uses = '5 * @classes.engineer.levels'

		if not found: ## CUSTOM (monkLevel)
			pattern = r'your monk level determines the number of points you have'
			if match := re.search(pattern, text):
				found = True
				uses = '@classes.monk.levels'

		if not found: ## CUSTOM (rage)
			pattern = r'you can enter a rage a number of times'
			if match := re.search(pattern, text):
				found = True
				lvl = '@classes.berserker.levels'
				uses = f'{lvl} < 3 ? 2 : {lvl} < 6 ? 3 : {lvl} < 12 ? 4 : {lvl} < 17 ? 5 : {lvl} < 20 ? 6 : 999'

		if True: ## CUSTOM, should not have uses
			pattern = r'you have ' + ncapt(sp_n) + r' (?:superiority dice|amplified shots|(?:\w+ )?points), instead of'
			pattern += r'|you regain all expended (?:force|tech) points when you'
			pattern += r'|you can[\'—]t use this feature on them again until'
			pattern += r'|they (?:cannot|can not|can[\'—]t) do so again until'
			pattern += r'|creature can[\'—]t (?:regain hit points|receive it) again (?:in this way )?until'
			pattern += r'|when you finish a long rest, roll two d20s'
			pattern += r'|borrowed luck roll'
			pattern += r'|you regain all of your expended uses of potent aptitude when you finish a short or long rest'
			pattern += r'|use this feature after the first, the dc'
			pattern += r'|it lasts until you (?:complete|finish)'
			pattern += r'|rest, you can (?:choose|replace)'
			if match := re.search(pattern, text):
				found = False

				recharge, uses = 'none', 0

		if (recharge != 'none') and not found:
			print(f'Failed to recognize uses count: on {name}')
			# print(f'{=}')
			for line in text.split('\n'):
				print(line)
			print('\n')
			raise ValueError
		if (recharge == 'none') and found:
			print(f'Recognized {uses=}, but failed to recognize recharge on {name}')
			# print(f'{=}')
			for line in text.split('\n'):
				print(line)
			print('\n')
			raise ValueError

	return uses, recharge

def getTarget(text, name):
	if text:
		text = text.lower()

		pattern = r'exhales [^.]*a (?P<size>\d+)-foot[- ](?P<shape>cone|line)'
		if match := re.search(pattern, text):
			return match['size'], 'ft', match['shape']

		pattern = r'(?P<size>\d+)-foot-radius,? \d+-foot-tall cylinder'
		if match := re.search(pattern, text):
			return match['size'], 'ft', 'cylinder'

		pattern = r'(?P<size>\d+)-foot[- ]radius(?P<sphere> sphere)?'
		if match := re.search(pattern, text):
			return match['size'], 'ft', ('sphere' if match['sphere'] else 'radius')

		pattern = r'(?P<size>\d+)-foot[- ](?P<shape>cube|square|line|cone)'
		if match := re.search(pattern, text):
			return match['size'], 'ft', match['shape']

	return None, '', ''

def getAction(text, name):
	action_type, damage, formula, save = '', { "parts": [], "versatile": '' }, '', ''

	if text:
		text = text.lower()

		## Power Attack
		pattern = r'make a (ranged|melee) (force|tech) attack'
		if (match := re.search(pattern, text)):
			if match.group(0) == 'ranged': action_type = 'rpak'
			else: action_type = 'mpak'

		## Saving Throw
		sp_ability = r'strength|dexterity|constitution|intelligence|wisdom|charisma'
		pattern = r'(?:must (?:first )?|can )?(?:succeed on|make|makes|if it fails) an? '
		pattern += r'(?P<save1>' + sp_ability + r')(?: or (?P<save2>' + sp_ability + r'))? saving throw'
		if (match := re.search(pattern, text)):
			action_type = action_type or 'save'
			#TODO find a way to use save1 or save2
			save = match.group('save1')[:3].lower()

		## Dice formula
		p_formula = r'(?P<dice>\d*d\d+)?\s*?\+?\s*?(?P<flat>\d+)?\s*?(?:\+ your (?P<ability_mod>(?:\w+ ){,5})(?:ability )?modifier)?'

		## Healing
		#TODO: temporary hit points
		pattern = r'(?:(?:(?:re)?gains?|restores|gaining|a number of) (?P<temp>temporary )?hit points equal to |hit points increase by )' + p_formula
		pattern2 = r'(?:(?:re)?gains?|restores?|gaining) (?:an extra )?' + p_formula + r' (?P<temp>temporary )?hit points'
		def foo(match):
			nonlocal action_type
			nonlocal damage
			dice, flat, ability_mod, temp = match.group('dice', 'flat', 'ability_mod', 'temp')

			if dice or flat or ability_mod:
				action_type = action_type or 'heal'
				formula = dice
				if flat:
					if formula: formula = f'{formula} + {flat}'
					else: formula = flat
				if ability_mod:
					formula = f'{formula or ""} + @mod'
				damage["parts"].append([ formula, 'temphp' if temp else 'healing' ])
				return 'FORMULA'
			else:
				return match.group(0)
		text = re.sub(pattern, foo, text)
		text = re.sub(pattern2, foo, text)

		## Damage
		pattern = r'(?:(?:takes?|taking|deals?|dealing) (?:(?:an )?(?:extra|additional) |up to )?|, | (?:and|plus) (?:another )?)(?:damage equal to )?' + p_formula + r'(?: of)?(?: (?P<type>\w+)(?:, (?:or )?\w+)*)?(?: damage|(?= [^\n]+ damage))'
		pattern2 = r'(?:the (?P<type>\w+ )?damage (?:also )?increases by|increase the damage by|(?:base|the additional) damage is|damage die becomes a) ' + p_formula
		def foo(match):
			nonlocal action_type
			nonlocal damage
			dice, flat, ability_mod = match.group('dice', 'flat', 'ability_mod')
			dmg_type = match.group('type') or '' if 'type' in match.groupdict() else ''

			if dice or flat or ability_mod:
				action_type = action_type or 'other'
				formula = dice
				if flat:
					if formula: formula = f'{formula} + {flat}'
					else: formula = flat
				if ability_mod:
					formula = f'{formula or ""} + @mod'
				damage["parts"].append([ formula, dmg_type ])
				return 'FORMULA'
			else:
				return match.group(0)
		text = re.sub(pattern, foo, text)
		text = re.sub(pattern2, foo, text)

		## 'Versatile' dice
		pattern = r'otherwise, it takes ' + p_formula
		if (match := re.search(pattern, text)):
			dice, flat, ability_mod = match.group('dice', 'flat', 'ability_mod')

			formula = dice
			if flat:
				if formula: formula = f'{formula} + {flat}'
				else: formula = flat
			if ability_mod:
				formula = f'{formula or ""} + @mod'
			damage["versatile"] = formula
		text = re.sub(pattern, r'FORMULA', text)

		## Other dice
		pattern = r'(?:roll(?:ing)?(?: a| two)?|choose to add|is reduced by(?: an amount equal to)?|which are|die(?:, a)?) ' + p_formula + r'(?<! )'
		pattern2 = r'for ' + p_formula + r' turns'
		text = re.sub(pattern, foo, text)
		text = re.sub(pattern2, foo, text)

		## Check for unprocessed dice
		pattern = r'\d*d\d+'
		def foo(match):
			nonlocal text
			nonlocal name

			pattern_ignore = r'on the d20|d20 roll|rolls? the d20'
			pattern_ignore += r'|uses a ' + match[0]
			pattern_ignore += r'|\|\s*' + match[0] + r'\s*\|' ## |d20|
			pattern_ignore += r'|\d*(?:d\d+)? to ' + match[0] ## 1 to d4, d4 to d6
			pattern_ignore += r'|' + match[0] + r' to \d*d\d+' ## d4 to d6
			pattern_ignore += r'|' + match[0] + r' at \d+th level' ## 4d8 at 11th level
			pattern_ignore += r'|th level \(' + match[0] + r'\)' ## 11th level (4d8)
			pattern_ignore += r'|increases by ' + match[0] + r' when you reach \d+th level' ## increases by 1d8 when you reach 11th level

			## TODO: Rework this to not use a hardcoded list
			if re.search(pattern_ignore, text) or name in ('Alter Self', 'Spectrum Bolt', 'Flow-Walking', 'Intercept'):
				return match[0]
			## TODO: Rework this to not use a hardcoded list
			elif name in ('Earthquake', 'Preparedness', 'Whirlwind', 'Will of the Force', 'Energetic Burst', 'Force Vision', 'Greater Feedback', 'Insanity', 'Climber', 'Lucky', 'Promising Commander', 'Polearm Specialist'):
				damage["parts"].append([ match[0], '' ])
			else:
				print(f'Unprocessed dice {match[0]} in {name}')
				print(f'{text=}')
				raise ValueError

			return 'FORMULA'
		re.sub(pattern, foo, text)

		action_type = action_type or 'other'

	return action_type, damage, formula, save

def getDuration(text, name):
	if text:
		text = text.lower()

		sp_units = r'(?P<unit>minute|hour|day|month|year|turn|round)s?'

		## "lasts for 1 minute"
		## "lasts for 8 hours"
		pattern = r'(?:^|\W)lasts for (?P<val>\d+) ' + sp_units + r'(?:\W|$)'
		if match := re.search(pattern, text):
			return match['val'], match['unit']

		## "for the next 8 hours"
		pattern = r'(?:^|\W)for the next (?P<val>\d+) ' + sp_units + r'(?:\W|$)'
		if match := re.search(pattern, text):
			return match['val'], match['unit']

		## "turned for 1 minute" (e.g. channel divinity)
		pattern = r'(?:^|\W)turned for (?P<val>\d+) ' + sp_units + r'(?:\W|$)'
		if match := re.search(pattern, text):
			return match['val'], match['unit']

		## "it is charmed by you for 1 minute"
		pattern = r'(?:^|\W)is \w+ by you for (?P<val>\d+) ' + sp_units + r'(?:\W|$)'
		if match := re.search(pattern, text):
			return match['val'], match['unit']

		## "For one minute"
		pattern = r'(?:^|\W)for one ' + sp_units + r'(?:\W|$)'
		if match := re.search(pattern, text):
			return 1, match['unit']

		## "until the end of your next turn"
		pattern = r'(?:^|\W)until the end of your next turn(?:\W|$)'
		if match := re.search(pattern, text):
			return 1, 'turn'

	return None, 'inst'

def raw(raw_item, attr):
	return raw_item[attr] if (attr and attr in raw_item) else None

def clean(raw_item, attr, default=''):
	item = raw(raw_item, attr) or default
	return cleanStr(item)

def cleanJson(raw_item, attr):
	item = clean(raw_item, attr+'Json', default='[]')
	try:
		item = json.loads(item)
	except:
		print(item)
		raise
	return item

def getProperty(prop_name, props):
	if prop_name not in props: return None

	def opt(p): return f'(?:{p})?'
	def capt(p, name): return f'(?P<{name}>{p})'

	prop = props[prop_name]

	if re.search('special', prop): return 'special'

	it = re.finditer(r'(\d+(?:,\d+)?)|(\d+d\d+)', prop)
	vals = [int(re.sub(',', '', val[1])) or val[2] for val in it]
	if len(vals) == 0: return True
	if len(vals) == 1: return vals[0]
	return vals
