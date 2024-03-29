import re, json, random, math, string, utils.config

def ncapt(patt): return f'(?:{patt})'
def capt(patt, name=None): return f'(?P<{name}>{patt})' if name else f'({patt})'
def exactly_x_times(pat, x): return fr'(?<!{pat}){pat}{{{x}}}(?!{pat})'


def cleanStr(string):
	if string:
		string = ' '.join(string.split(' ')) or ''
		string = re.sub(r'’', r"'", string) or ''
		string = re.sub(r'\ufffd', r'—', string) or ''
		string = re.sub(r'(\\+r|\\*\r)+', r'', string) or ''
		string = re.sub(r'(\\+n|\\*\n)+', r'\n', string) or ''
		return string

def cleanRecursive(obj, depth=0):
	if depth > 100: return obj
	if type(obj) == str:
		obj = cleanStr(obj)
		try:
			s = int(obj)
			if f'{s}' == obj:
				obj = s
		except:
			pass
		return obj
	if type(obj) == dict:
		return {
			cleanRecursive(key, depth+1): cleanRecursive(obj[key], depth+1)
			for key in obj
		}
	if type(obj) in (list, tuple):
		return [ cleanRecursive(val, depth+1) for val in obj ]
	return obj

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

			## Add inline rolls
			lines[i] = re.sub(r'\b((?:\d*d)?\d+\s*)x(\s*\d+)\b', r'\1*\2', lines[i])
			lines[i] = re.sub(r'\b(\d*d\d+(?:\s*[+*]\s*\d+)?)\b', r'[[/r \1]]', lines[i])
		return '\n'.join(lines)

def makeTable(content, header=None, align=None):
	table = ''
	if header:
		line = ''
		for x in range(len(header)):
			part = header[x]
			if align and align[x]: part = f'<th align="{align[x]}">{part}</th>'
			else: part = f'<th>{part}</th>'
			line += part
		line = f'<thead><tr>{line}</tr></thead>'
		table += line

	if content:
		contents = ''
		for y in range(len(content)):
			line = ''
			for x in range(len(content[y])):
				part = content[y][x]
				if align and align[x]: part = f'<th align="{align[x]}">{part}</th>'
				else: part = f'<th>{part}</th>'
				line += part
			line = f'<tr class="rows">{line}</tr>'
			contents += line
		contents = f'<tbody>{contents}</tbody>'
		table += contents

	table = f'<table>{table}</table>'
	return table

def makeRollTable(table, name):
	if table:
		content = [ (
			opt["roll"],
			(opt["name"] or '') + (': ' if (opt["name"] and opt["description"]) else '') + (opt["description"] or '')
		) for opt in table ]
		header = [ f'[[/r d{len(content)} # {name}]]', name ]
		align = [ 'center', 'center' ]
		return makeTable(content, header=header, align=align)

def getActivation(text, uses, recharge):
	if text:
		text = text.lower()

		if re.search(r'as a reaction|you can use your reaction|using your reaction|you can use this special reaction|reaction on your turn', text):
			return 'reaction'
		elif re.search(r'bonus action', text):
			return 'bonus'
		elif re.search(r'as an action|can take an action|you can use your action', text):
			return 'action'
		elif uses or recharge:
			return 'special'
	return None

def getUses(text, name):
	uses, recharge = None, None

	found = False

	if text:
		text = text.lower()
		text, _ = getStatblocks(text)

		patSR = r'(finish|finishes|complete|after) a short(?: rest)?(?: or(?: a)? long rest)'
		patSR += r'|regains? all expended (?:uses|charges) (?:on|after) a short(?: or long)? rest'
		patLR = r'(finish|finishes|complete) a long rest'
		patLR += r'|regains? all expended (?:uses|charges) (?:on|after) a long rest'
		patRC = r'until you move 0 feet on one of your turns'
		patRC += r'|until you (?:store|reload|recover)'
		patRC += r'|regains? all expended (?:uses|charges) when you (?:store|reload|recover)'

		if re.search(patSR, text): recharge = 'sr'
		elif re.search(patLR, text): recharge = 'lr'
		elif re.search(patRC, text): recharge = 'charges'

		if not found: ## BASE +/* ABILITY modifier times, min of MIN
			pattern = r'(?<!gain )a (?:combined |maximum )?number of (?:power surges |sentries |(?P<times>times?) )?equal to (?:(?P<base>\d+) \+ )?(?P<half>half )?your '
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

				uses = f'@abilities.{uses_ability1}.mod'
				if uses_ability2: uses = f'max({uses}, @abilities.{uses_ability2}.mod)'

				if uses_base: uses = f'{uses_base} + {uses}'
				if uses_min: uses = f'max({uses}, {uses_min})'
				if uses_half:
					if uses_rounded == 'up':
						uses = f'ceil(({uses})/2)'
					elif uses_rounded == 'down':
						uses = f'floor(({uses})/2)'
					else:
						uses = f'round(({uses})/2)'

		if not found: ## PROF times
			pattern = r'a (?:combined )?number of (?:times|charges|superiority dice|(?:force|tech) points in this way) equal to (?P<half>half )?your proficiency bonus'
			pattern += r'|in excess of (?P<half2>half )?your proficiency bonus \(resetting on a long rest\)'

			if match := re.search(pattern, text):
				found = True

				uses = '@attributes.prof'
				if match['half'] or match['half2']:
					uses = f'round({uses}/2)'

		if not found: ## CLASS LEVEL times
			pattern = r'a (?:combined )?number of (?:times|charges) equal to (?P<half>half )?your (?P<class>\w+) level(?: \(rounded (?P<round>up|down)\))?'

			if match := re.search(pattern, text):
				found = True

				uses = f'@classes.{match["class"].lower()}.levels'
				if match['half']:
					if match['round'] == 'up':
						uses = f'ceil(({uses})/2)'
					elif match['round'] == 'down':
						uses = f'floor(({uses})/2)'
					else:
						uses = f'round(({uses})/2)'

		sp_action = r'use (?:it|(?:this|each|the chosen|these) (?:features?|traits?|abilit(?:y|ies)))'
		sp_action += r'|initiate playing an enhanced song'
		sp_action += r'|invoke each of your totems'
		sp_action += r'|invoke a totem this way'
		sp_action += r'|create a panacea'
		sp_action += r'|manifest your ideals'
		sp_action += r'|(?:cast|do) (?:it|so)'
		sp_action += r'|activate'

		sp_action_past = r'used? (?:it|(?:this|each|the chosen|these) (?:features?|traits?|abilit(?:y|ies)))'
		sp_action_past += r'|initiated? playing an enhanced song'
		sp_action_past += r'|invoked? each of your totems'
		sp_action_past += r'|invoked? a totem this way'
		sp_action_past += r'|created? a panacea'
		sp_action_past += r'|manifest(?:ed)? your ideals'
		sp_action_past += r'|(?:cast|do(?:ne)?) (?:it|so)'
		sp_action_past += r'|activated?'

		sp_n = r'one|two|three|four|five|six|seven|eight|nine|ten|\d+'
		sp_n_times = capt(sp_n) + r' times|(once|twice|thrice)'

		if not found: ## class/archetype table
			pattern = fr'(?:points you have,|number of times|more times at higher levels) as shown (?:for your (?:[\w-]+ )+level )?in the (?P<column>(?:[\w-]+ )+)column of the (?P<table>(?:[\w-]+ )+)table'
			if match := re.search(pattern, text):
				found = True
				uses = f'@scale.{slugify(match["table"], capitalized=False, space="-")}.{slugify(match["column"], capitalized=False, space="-")}'

		if not found: ## NUMBER times
			pattern = fr'you (?:can|may) {ncapt(sp_action)} (?:a (?:combined )?(?:total of )?)?{ncapt(sp_n_times)}'
			pattern += fr'|(?:you (?:have|gain)|(?:this|the) \w+ (?:has|gains)) {capt(sp_n)} (?:superiority dic?e|amplified shots|(?!hit)(?:\w+ )?points|charges)'

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
			pattern = fr'once (you([\'—]ve| have)?|the \w+ (has|have) been|your companion has) {ncapt(sp_action_past)}'
			pattern += fr'|you (can[\'—]t|cannot|can not) {ncapt(sp_action)} (again )?until'
			pattern += fr'|if you {ncapt(sp_action)} again before'
			pattern += fr'|rest before you can {ncapt(sp_action)} again'

			if match := re.search(pattern, text):
				found = True

				uses = 1

		if not found: ## CUSTOM (twiceScoutLevelPlusInt)
			pattern = r'that barrier has hit points equal to twice your scout level \+ your intelligence modifier'
			if match := re.search(pattern, text):
				found = True
				uses = '2 * @classes.scout.levels + @abilities.int.mod'

		if not found: ## CUSTOM (twiceConsularLevelPlusWisOrCha)
			pattern = r'the barrier has hit points equal to twice your consular level \+ your wisdom or charisma modifier \(your choice\)'
			if match := re.search(pattern, text):
				found = True
				uses = '2 * @classes.consular.levels + max(@abilities.wis.mod, @abilities.cha.mod)'

		if not found: ## CUSTOM (EngineerLevel)
			pattern = r'has (?:a number of )?hit points equal to (?P<five>5 x )?your engineer level'
			if match := re.search(pattern, text):
				found = True
				uses = '@classes.engineer.levels'
				if match["five"]: uses = f'5 * {uses}'

		if True: ## CUSTOM, should not have uses
			pattern = fr'you have {ncapt(sp_n)} (?:superiority dice|amplified shots|(?:\w+ )?points), instead of'
			pattern += r'|you regain all expended (?:force|tech) points when you'
			pattern += r'|you can[\'—]t use this feature on them again until'
			pattern += r'|they (?:cannot|can not|can[\'—]t) do so again until'
			pattern += r'|creature can[\'—]t (?:regain hit points|receive it) again (?:in this way )?until'
			pattern += r'|rest before they can do so again'
			pattern += r'|when you finish a long rest, roll two d20s'
			pattern += r'|borrowed luck roll'
			pattern += r'|you regain all of your expended uses of potent aptitude when you finish a short or long rest'
			pattern += r'|use this feature after the first, the dc'
			pattern += r'|it lasts until you (?:complete|finish)'
			pattern += r'|rest, you can (?:choose|replace|change|modify|create)'
			pattern += r'|rest, you must make a '
			pattern += r'|rest, you gain'
			pattern += r'|feature after you complete a short or long rest'
			pattern += r'|until you complete a (?:short|long) rest'
			if match := re.search(pattern, text):
				found = False

				recharge, uses = None, None

		if recharge and not found:
			print(f'Failed to recognize uses count: on {name}')
			# print(f'{=}')
			for line in text.split('\n'):
				print(line)
			print('\n')
			raise ValueError
		if not recharge and found:
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
			return int(match['size']), 'ft', match['shape']

		pattern = r'(?P<size>\d+)-foot-radius,? \d+-foot-tall cylinder'
		if match := re.search(pattern, text):
			return int(match['size']), 'ft', 'cylinder'

		pattern = r'(?P<size>\d+)-foot[- ]radius(?P<sphere> sphere)?'
		if match := re.search(pattern, text):
			return int(match['size']), 'ft', ('sphere' if match['sphere'] else 'radius')

		pattern = r'(?P<size>\d+)-foot[- ](?P<shape>cube|square|line|cone)'
		if match := re.search(pattern, text):
			return int(match['size']), 'ft', match['shape']

		pattern = r'choose (?:one|a) (?P<attitude> hostile| allied)?(?P<type>creature|droid|ally|enemy|object|starship)'
		if match := re.search(pattern, text):
			if match['attitude'] == 'hostile': return 1, '', 'enemy'
			elif match['attitude'] == 'allied': return 1, '', 'ally'
			else: return 1, '', match['type']

	return None, '', ''

def getRange(text, name):
	pattern = r'within (?P<value>\d+) (?P<unit>\w+)'
	if match := re.search(pattern, text):
		return match["value"], match["unit"]

	return None, ''

def getAction(text, name, scale=None, rolled_formula='@ROLLED'):
	action_type, damage, other_formula, save, save_dc, scaling = '', { "parts": [], "versatile": '' }, '', '', None, { "mode": 'none'}

	has_rolled = False

	if text:
		text = text.lower()
		text, _ = getStatblocks(text)

		## Power Attack
		pattern = r'(make|making) a (?P<range>ranged|melee) (force|tech) attack'
		if (match := re.search(pattern, text)):
			if match['range'] == 'ranged': action_type = 'rpak'
			else: action_type = 'mpak'

		## Saving Throw
		sp_ability = r'strength|dexterity|constitution|intelligence|wisdom|charisma'
		pattern = r'(?:succeed on|make|makes|if it fails) (?:an? )?(dc (?P<dc>\d+) )?'
		pattern += fr'(?P<save1>{sp_ability})(?: or (?P<save2>{sp_ability}))? saving throws?'
		pattern += r'(?: \(dc (?P<dc2>\d+)\))?'
		def saving_throw(match):
			nonlocal action_type, save, save_dc
			action_type = action_type or 'save'
			#TODO find a way to use save1 or save2
			save = save or match['save1'][:3].lower()
			save_dc = save_dc or int(match["dc"]) if match["dc"] else int(match["dc2"]) if match["dc2"] else None
			return 'SAVINGTHROW'
		text = re.sub(pattern, saving_throw, text)

		## Dice formula
		p_plus = r'(?:\s*\+\s*)'
		p_mult = r'(?:(?P<mult>\d+) (?:times|x|\*)\s+)'
		p_dice = r'(?P<dice>\d*d\d+(?:\s*\+\s*\d*d\d+)*)'
		p_rolled = r'(?P<rolled>(?:the )?(?:number|amount) (?:rolled|you roll)(?: on (?:the|your) \w+ die)?|(?:the|your) \w+ die|the (?:\w+ )?die roll(?:ed)?|the (?:(?:result of the )?roll|result))'
		p_dice = fr'(?:{p_dice}|{p_rolled})'
		p_flat = fr'(?:{p_plus}?(?P<flat>\d+))'
		p_mod = fr'(?:{p_plus}?your (?P<ability_mod>\w[\w ]*?)(?: ability)? modifier)'
		p_charlvl = fr'(?:{p_plus}?(?P<char_level>your level))'
		p_classlvl = fr'(?:{p_plus}?your (?P<class_level>\w[\w ]*?)(?: class)? level)'
		p_mod2 = fr'(?:{p_plus}?your (?P<ability_mod2>\w[\w ]*?)(?: ability)? modifier)'
		p_prof = fr'(?P<prof_bonus>{p_plus}?your proficiency bonus)'

		p_formula = fr'{p_mult}?{p_dice}?{p_flat}?{p_mod}?{p_charlvl}?{p_classlvl}?{p_mod2}?{p_prof}?'
		p_dformula = fr'{p_mult}?{p_dice}{p_flat}?{p_mod}?{p_charlvl}?{p_classlvl}?{p_mod2}?{p_prof}?'

		def get_formula(match):
			nonlocal rolled_formula, has_rolled
			mult = match.groupdict().get('mult')
			dice = match.groupdict().get('dice')
			rolled = match.groupdict().get('rolled')
			flat = match.groupdict().get('flat')
			ability_mod = match.groupdict().get('ability_mod')
			char_lvl = match.groupdict().get('char_level')
			class_lvl = match.groupdict().get('class_level')
			ability_mod2 = match.groupdict().get('ability_mod2')
			prof_bonus = match.groupdict().get('prof_bonus')

			if dice and dice.startswith('d'): dice = f'1{dice}'
			if dice or rolled or flat or ability_mod or class_lvl:
				formula = dice
				if rolled and not has_rolled and rolled_formula != '@ROLLED':
					has_rolled = True
					if formula: formula = f'{formula} + {rolled_formula}'
					else: formula = rolled_formula
				if flat:
					if formula: formula = f'{formula} + {flat}'
					else: formula = flat
				if ability_mod:
					mod = '@mod'
					if ability_mod in ('strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma'):
						mod = f'@abilities.{ability_mod[:3]}.mod'
					if formula: formula = f'{formula} + {mod}'
					else: formula = mod
				if char_lvl:
					lvl = f'@details.level'
					if formula: formula = f'{formula} + {lvl}'
					else: formula = lvl
				if class_lvl:
					lvl = f'@classes.{class_lvl.lower()}.levels'
					if formula: formula = f'{formula} + {lvl}'
					else: formula = lvl
				if ability_mod2:
					mod = '@mod'
					if ability_mod2 in ('strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma'):
						mod = f'@abilities.{ability_mod2[:3]}.mod'
					if formula: formula = f'{formula} + {mod}'
					else: formula = mod
				if prof_bonus:
					bonus = '@prof'
					if formula: formula = f'{formula} + {bonus}'
					else: formula = bonus
				if formula and mult: formula = f'{mult} * ({formula})'
				return formula

		## Healing
		patterns = [fr'(?:(?:(?:re)?gains?|restores|gaining|a number of|granting them|grant a number of creatures? (?:up|equal) to(?: \w+)+?|give yourself or that friendly creature) (?P<temp>temporary )?hit points equal to |hit points increase by ){p_formula}']
		patterns += [fr'(?:(?:re)?gains?|restores?|gaining) (?:an extra )?{p_formula} (?:extra |additional )?(?P<temp>temporary )?hit points']
		patterns += [fr'(?P<temp>reduces?) the damage (?:taken )?by (?:an extra )?{p_formula}']
		def healing(match):
			nonlocal action_type, damage

			formula = get_formula(match)
			if formula:
				temp = match['temp']
				action_type = action_type or 'heal'
				damage["parts"].append([ formula, 'temphp' if temp else 'healing' ])
				return 'FORMULA'
			else:
				return match.group(0)
		for pat in patterns: text = re.sub(pat, healing, text)

		## Damage
		opt1 = fr'(?:takes?|taking|deals?|dealing|do|suffer)(?:(?: an)? (?:extra|additional)| up to)?'
		opt2 = fr','
		opt3 = fr'(?:and|plus|weapon\'s damage dice \+)(?: another| an extra)?'
		prefix1 = fr'(?:{opt1}|{opt2}|{opt3})(?: (?P<type>\w+)? ?damage(?: to the creature)? equal to)?'
		prefix2 = fr'(?:{opt1})(?: (?P<type>\w+)? ?damage(?: to the creature)? equal to)'
		posfix1 = fr'(?:of )?(?:(?P<type2>\w+)?(?:,(?: or)? \w+)*)?(?: ?damage| (?=[^.]+ damage))'

		opt1 = fr'the (?P<type>\w+ )?damage (?:also )?increases by'
		opt2 = fr'increase the damage by'
		opt3 = fr'(?:base|the additional|the extra) damage is'
		opt4 = fr'damage die becomes a'
		prefix3 = fr'(?:{opt1}|{opt2}|{opt3}|{opt4})'

		patterns = [fr'{prefix1} \d+ \({p_formula}\) {posfix1}']
		patterns += [fr'{prefix2} \d+ \({p_formula}\)']
		patterns += [fr'{prefix3} \d+ \({p_formula}\)']
		patterns += [fr'{prefix1} {p_formula} {posfix1}']
		patterns += [fr'{prefix2} {p_formula}']
		patterns += [fr'{prefix3} {p_formula}']
		patterns += [fr'the (?P<type>\w+) damage (?:equals|is equal to) {p_formula}']
		def dmg(match):
			nonlocal action_type, damage, other_formula

			formula = get_formula(match)
			if formula:
				dmg_type = match.groupdict().get('type') or match.groupdict().get('type2') or ''
				action_type = action_type or 'other'
				if dmg_type == '' and formula == rolled_formula:
					other_formula = formula
				else:
					damage["parts"].append([ formula, dmg_type ])
				return 'FORMULA'
			else:
				return match.group(0)
		for pat in patterns: text = re.sub(pat, dmg, text)

		## 'Versatile' dice
		patterns = [fr'otherwise, it takes {p_dformula}']
		patterns += [fr', or \d+ \({p_formula}\)(?= [^.]+ damage)']
		patterns += [fr', or {p_formula}(?= [^.]+ damage)']
		def versatile(match):
			formula = get_formula(match)
			damage["versatile"] = formula
		for pat in patterns: text = re.sub(pat, versatile, text)

		## Ability Check
		patterns = [fr'to make a (?P<type>(?:universal|light|dark) force|tech)casting ability check(?P<proficient> with proficiency)?']
		def ability_check(match):
			nonlocal action_type, other_formula

			ctype = match.groupdict().get('type')
			prof = match.groupdict().get('proficient')

			if ctype:
				dmg_type = match.groupdict().get('type') or match.groupdict().get('type2') or ''
				action_type = action_type or 'abil'

				ability = '@mod'
				if ctype == 'universal force': ability = 'max(@abilities.wis.mod, @abilities.cha.mod)'
				elif ctype == 'light force': ability = '@abilities.wis.mod'
				elif ctype == 'dark force': ability = '@abilities.cha.mod'
				elif ctype == 'tech': ability = '@abilities.int.mod'

				other_formula = f'1d20 + {ability}'
				if prof: other_formula += ' + @prof'

				return 'FORMULA'
			else:
				return match.group(0)
		for pat in patterns: text = re.sub(pat, ability_check, text)

		## Other dice
		prefixes = fr'roll(?:ing)?(?: a| two)?'
		prefixes += fr'|choose to add'
		prefixes += fr'|(?:(?:is|are) (?:reduced|increased)|(?:increases|reduces) their current(?: and maximum)? \w+ points) by(?: an amount equal to)?'
		prefixes += fr'|which are'
		prefixes += fr'|die(?:, a)?'

		p_roll_types = fr'(?:(?:damage |attack )?rolls?|(?:ability )?checks?|results?|saving throws?|levels?|totals?|damage|attack|save)'
		patterns = [fr'(?:{prefixes}) (?:an additional )?{p_dformula}(?<! )']
		patterns += [fr'for {p_dformula} (?:turns|days)']
		patterns += [fr'a {p_dformula} that you can roll']
		patterns += [fr'{p_dformula}(?: tiny projectiles| such fissures|(?:\s*x\s*\d+\s+)?feet)']
		patterns += [fr'\|\s*{p_dformula}\s*\|']
		patterns += [fr'it deploys {p_dformula}']
		patterns += [fr'move (?:to a(?:n unoccupied)? space (?:you can see )?up to )?(?:a(?:n additional)? distance|a number of feet) equal to {p_dformula}']
		patterns += [fr'speed increases by {p_dformula}']
		patterns += [fr'{p_dformula} to it\'?s movement speed']
		patterns += [fr'a number of rounds equal to {p_dformula}']
		patterns += [fr'bonus to (?:any|all|every|the next) {p_roll_types}(?: (?:you|they|it) makes?)? equal to {p_dformula}']
		patterns += [fr'(?:add|subtract)(?:ing|s)? {p_dformula} (?:to|from) (?:any|all|every|(?:both )?the(?: next)?|their|your|it\'s) {p_roll_types}(?: (?:you|they|it) makes?)?']
		patterns += [fr'the result of (?:your|their|it\'s) {p_roll_types} (?:plus|minus) {p_dformula}']
		patterns += [fr'(?P<rolled>(?:expend|roll) (?:a|one|the) \w+ die(?: and roll it)?,? (?:and |to )?add(?:ing)? (?:it )?to the {p_roll_types})']
		patterns += [fr'(?P<rolled>up to the result of the roll)']
		patterns += [fr'(?P<rolled>roll(?:ing)? (?:the|a)(?: \w+)? die and (?:(?:add|subtract)(?:ing|\'s)?|plus|minus) (?:it|the (?:(?:amount|number) rolled|rolled (?:amount|number)|result)) (?:from|to|is))']
		patterns += [fr'(?P<rolled>the (?:\w+ die|(?:amount|number) (?:you )?rolled|rolled (?:amount|number)|result) is (?:added|subtracted) (?:from|to))']
		def simple(match):
			nonlocal action_type, damage, other_formula

			formula = get_formula(match)
			if formula:
				action_type = action_type or 'other'
				if other_formula == formula: pass
				elif other_formula == '': other_formula = formula
				else: damage["parts"].append([ formula, '' ])
				return 'FORMULA'
			else:
				return match.group(0)
		for pat in patterns: text = re.sub(pat, simple, text)

		## Check for unprocessed dice
		pattern = r'\d*d\d+'
		def unprocessed(match):
			nonlocal text, name

			dice = match[0]

			pattern_ignore = fr'on the d20|d20 (?:roll|result)|roll(?:ing|s)? (?:(?:of )?the|a) d20|{dice}s'
			pattern_ignore += fr'|which is a {dice}'
			pattern_ignore += fr'|uses a {dice}'
			pattern_ignore += fr'|(?:versatile|barbed|gauntleted|spiked|double) \({dice}\)(?: and \w+(?: \d+)?)? propert(?:y|ies)' ## versatile (2d4) property
			pattern_ignore += fr'|\|\s*{dice}\s*\|' ## |d20|
			pattern_ignore += fr'|\d*(?:d\d+)? to (?:a )?{dice}' ## 1 to d4, d4 to d6
			pattern_ignore += fr'|{dice} to (?:a )?\d*d\d+' ## d4 to d6
			pattern_ignore += fr'|{dice} at \d+th level' ## 4d8 at 11th level
			pattern_ignore += fr'|th level \({dice}\)' ## 11th level (4d8)
			pattern_ignore += fr'|increasing by {dice} for each round' ## increasing by 1d8 for each round you do not detonate it
			pattern_ignore += fr'|increases by {dice} when you reach \d+th level' ## increases by 1d8 when you reach 11th level
			pattern_ignore += fr'|(?:recovers|regains) {dice} charges'
			pattern_ignore += fr'|it contains {dice}(?: [+-] \d+)? levels'
			pattern_ignore += fr'|plus {dice} for each slot level'
			pattern_ignore += fr'|to a maximum of {dice}'
			pattern_ignore += fr'|more than {dice} additional damage'
			pattern_ignore += fr'|instead of restoring {dice} hit points'
			pattern_ignore += fr'|a {dice} instead of expending'
			pattern_ignore += fr'|add(?: a)? {dice} to (?:a|an|any|its|the) (?:ability checks)?(?: or )?(?:saving throws?)?(?:rolls?)?'
			pattern_ignore += fr'|rolls(?: a)? {dice} and subtracts the number rolled'
			pattern_ignore += fr'|instead of its {dice}\.'
			pattern_ignore += fr'|becomes {dice}\.'

			if dice and dice.startswith('d'): dice = f'1{dice}'
			formula = dice

			if re.search(pattern_ignore, text):
				return formula
			else:
				raise ValueError(f'Unprocessed dice {formula} in {name}', text)

			return 'FORMULA'
		text = re.sub(pattern, unprocessed, text)

		action_type = action_type or 'other'

	if scale:
		scale = scale.lower()
		scaling["mode"] = "level" if re.search(r'force potency|overcharge tech', scale) else "atwill"

		if scaling["mode"] == "atwill" and len(damage["parts"]) == 1:
			if initial_match := re.search(r'd(?P<die>\d+)', damage["parts"][0][0]):
				initial_die = int(initial_match["die"])
				first_change, prev, prevdiff, cur, diff = None, None, None, None, None
				pattern = fr'a d(?P<die>\d+) at (?P<lvl>\d+)(?:st|nd|rd|th) level'
				if re.search(pattern, scale):
					for match in re.finditer(pattern, scale):
						cur = int(match["die"]), int(match["lvl"])
						if not first_change: first_change = cur[1]
						if prev: diff = cur[0]-prev[0], cur[1]-prev[1]
						if prevdiff and (prevdiff != diff): break
						prevdiff = diff
						prev = cur
					else:
						die_diff, level_diff = prevdiff
						scaled_die = f'd({initial_die}+{die_diff}*floor((@details.level+{level_diff - first_change})/{level_diff}))'
						damage["parts"][0][0] = re.sub(fr'd{initial_die}', scaled_die, damage["parts"][0][0], 1)

		pattern = r'increases by (?P<die>\d*d\d+) for each slot level above'
		if match := re.search(pattern, scale): scaling["formula"] = match["die"]

	return action_type, damage, other_formula, save, save_dc, scaling

def getDuration(text, name):
	if text:
		text = text.lower()

		sp_units = r'(?P<unit>minute|hour|day|month|year|turn|round)s?'

		## "lasts for 1 minute"
		## "for the next 8 hours"
		## "turned for 1 minute" (e.g. channel divinity)
		## "it is charmed by you for 1 minute"
		pattern = fr'(?:^|\W)for (?:the next )?(?:(?P<val>\d+) |one )?{sp_units}(?:\W|$)'
		if match := re.search(pattern, text):
			return match['val'] or 1, match['unit']

		## "once within the next 10 minutes"
		pattern = fr'(?:^|\W)once (?:with)?in the next (?:(?P<val>\d+) )?{sp_units}(?:\W|$)'
		if match := re.search(pattern, text):
			return match['val'] or 1, match['unit']

		## "until the end of your next turn"
		pattern = r'(?:^|\W)until the end of your next turn(?:\W|$)'
		if match := re.search(pattern, text):
			return 1, 'turn'

	return None, 'inst'

def raw(raw_item, attr):
	return raw_item[attr] if (attr and attr in raw_item) else None

def clean(raw_item, attr, default=''):
	item = raw(raw_item, attr)
	if item == None: item = default
	item = cleanRecursive(item)
	return item

def cleanJson(raw_item, attr, default='{}'):
	item = clean(raw_item, attr+'Json', default=default)
	if item == '' or item == None: item = default
	try:
		item = json.loads(item)
	except:
		print(repr(item))
		raise
	item = cleanRecursive(item)
	return item

def getProperty(prop_name, props):
	if prop_name not in props: return None

	def opt(p): return f'(?:{p})?'
	def capt(p, name): return f'(?P<{name}>{p})'

	prop = props[prop_name]

	if re.search('special', prop): return 'special'

	it = re.finditer(r'(\d+d\d+)|(\d+(?:,\d+)?)', prop)
	vals = [val[1] or int(re.sub(',', '', val[2])) for val in it]
	if len(vals) == 0: return True
	if len(vals) == 1: return vals[0]
	return vals

def getProperties(targets, props_list, strict=False, error=False, needs_end=False, verbose=False):
	if not targets: return {}
	if type(targets) == str: targets = (targets,)
	if len(props_list) == 0: raise ValueError(targets, props_list, strict, error, needs_end)

	props = [prop["name"] for prop in props_list]

	pname_pat = fr'(?:{"|".join(props)})'
	if not strict: pname_pat = pname_pat.lower()
	pval_pat = r'(?: (?:\d+)| \((?:[^()]+)\))?'
	pval_pat_ = r'(?: (?P<flat>\d+)| \((?P<values>[^()]+)\))?'
	prop_pat = fr'(?:{pname_pat}(?=\W|$){pval_pat})'
	props_pat = fr'(?:{prop_pat}(?:, {prop_pat})*(?: and {prop_pat})?)'

	pattern = fr'(?P<neg>removes the )?(?P<props>{props_pat})(?: propert(?:y|ies))'
	if not needs_end: pattern += '?'

	properties = {}

	for target in targets:
		if target == '—': continue

		if not strict: target = target.lower()
		if re.search(pattern, target):
			for match in re.finditer(pattern, target):
				text = match['props']
				if verbose:
					print(f'		{match=}')
					print(f'		{text=}')
				for prop in props_list:
					pName = prop["name"] if strict else prop["name"].lower()
					pId = prop["id"]
					pattern2 = fr'{pName}(?=\W|$){pval_pat_}'
					def foo(match2):
						if verbose:
							print(f'		{match2=}')
							print(f'		{match2.groupdict()=}')
						if match2[0].find('MATCH') != -1: return 'MATCH'
						if match['neg']:
							properties[pId] = False
						else:
							if match2['flat']:
								properties[pId] = int(match2['flat'])
							elif match2['values']:
								properties[pId] = match2['values']
							else:
								properties[pId] = True
						return 'MATCH'
					text = re.sub(pattern2, foo, text)
		elif error:
			print(f'{props_list=}')
			print(f'{target=}')
			print(f'{targets=}')
			raise ValueError()
	return properties

def getStatblocks(text):
	lines = text.split('\n')
	text = ''
	statblocks = []

	statblock = ''
	for line in lines:
		if statblock == '':
			if (text == '___\n' or text.endswith('\n___\n')) and line.startswith('>'):
				statblock = '___\n' + line
				text = text[:-4]
		elif not line.startswith('>'):
			statblocks += [statblock]
			statblock = ''

		if statblock == '':
			text += line + '\n'

	return text, statblocks

def getTraits(text, name, require_prefix=True, restrict_types=None):
	_text = text
	choices, grants = [], []

	if text:
		types = {
			"skills": { skl["name"].lower(): skl for skl in utils.config.skills },
			"saves": { attr["name"].lower(): attr for attr in utils.config.attributes },
			"tools": { tool["name"].lower(): tool for tool in utils.config.tools },
			"weapons": {
				wpn: {
					"name": wpn,
					"id": re.sub(' -', '', wpn),
					"type": (
						'melee' if wpn_class in ["blade", "crushing", "trip"] else
						'ranged' if wpn_class in ["carbine", "heavy", "rifle", "sidearm"] else
						''
					),
				} for wpn_class in utils.config.weapon_classes.values() for wpn in wpn_class
			},
			"armors": { armor["name"].lower(): armor for armor in utils.config.armor_types },
		}
		for t in types:
			for trait in dict(types[t]):
				types[t][getPlural(trait)] = types[t][trait]

		generic_types = {
			"skills": {
				attr["name"].lower(): { "foo": lambda trait, skl: skl["attr"] == types["saves"][trait]["id"] }
				for attr in utils.config.attributes
			},
			"tools": {
				"musical instrument": { "id": 'music:*' },
				"instrument": { "id": 'music:*' },
				"kit": { "id": 'specialist:*' },
				"specialist's kit": { "id": 'specialist:*' },
				"artisan's implement": { "id": 'artisan:*' },
				"gaming set": { "id": 'game:*' },
				"vehicle": { "id": 'vehicle:*' },
			},
			"weapons": {
				"vibroweapon": { "ids": [ 'svb:*', 'mvb:*' ] },
				"simple or martial vibroweapon": { "ids": [ 'svb:*', 'mvb:*' ] },
				"simple vibroweapon": { "id": 'svb:*' },
				"martial vibroweapon": { "id": 'mvb:*' },
				"exotic vibroweapon": { "id": 'evw:*' },

				"lightweapon": { "ids": [ 'slw:*', 'mlw:*' ] },
				"simple or martial lightweapon": { "ids": [ 'slw:*', 'mlw:*' ] },
				"simple lightweapon": { "id": 'slw:*' },
				"martial lightweapon": { "id": 'mlw:*' },
				"exotic lightweapon": { "id": 'elw:*' },

				"blaster": { "ids": [ 'smb:*', 'mrb:*' ] },
				"simple or martial blaster": { "ids": [ 'smb:*', 'mrb:*' ] },
				"simple blaster": { "id": 'smb:*' },
				"martial blaster": { "id": 'mrb:*' },
				"exotic blaster": { "id": 'exb:*' },
				# TODO: Find a way to make this work
				"blaster that deal sonic damage": { "ids": [ 'smb:*', 'mrb:*' ] },
				"blasters that deal sonic damage": { "ids": [ 'smb:*', 'mrb:*' ] },

				"improvised weapon": { "id": 'imp' },

				"simple weapon": { "ids": [ 'svb:*', 'slw:*', 'smb:*' ] },
				"martial weapon": { "ids": [ 'mvb:*', 'mlw:*', 'mrb:*' ] },
				"martial light- and vibro- weapon": { "ids": [ 'mvb:*', 'mlw:*' ] },
				"exotic weapon": { "ids": [ 'evw:*', 'elw:*', 'exb:*' ] },
			},
			"saves": {
				"saving throw": { "id": "*" },
				"saving throws using the chosen ability": { "id": '*' },
			}
		}
		for t in generic_types:
			for trait in dict(generic_types[t]):
				generic_types[t][getPlural(trait)] = generic_types[t][trait]

		types_ids = { t: t for t in types }
		types_ids["armors"] = "armor"
		types_ids["tools"] = "tool"
		types_ids["weapons"] = "weapon"

		p_types = {}
		cp_types = {}
		for k in types:
			if restrict_types and k not in restrict_types: continue
			values = [ f'{trait}' for trait in reversed(types[k]) ]
			p_types[k] = ncapt(ncapt('|'.join(values)) + fr'(?: {k}?)?')
			cp_types[k] = ncapt(capt('|'.join(values), name=f'type_{k}') + fr'(?: {k}?)?')
			if k in generic_types:
				generic_values = [ f'{k}?' ] + [ f'{trait}' for trait in reversed(generic_types[k]) ]
				p_types["generic_"+k] = ncapt(fr'(?:all )?' + ncapt('|'.join(generic_values)) + fr'(?: {k}?)?')
				cp_types["generic_"+k] = ncapt(fr'(?P<all_{k}>all )?' + capt('|'.join(generic_values), name=f'gtype_{k}') + fr'(?: {k}?)?')
		for t in generic_types: generic_types[t][t] = { "id": f'*' }

		p_types["all"] = ncapt('|'.join([p_types[k] for k in p_types]))
		cp_types["all"] = ncapt('|'.join([cp_types[k] for k in cp_types]))

		p_trait_types = ncapt('|'.join(f'{t}?' for t in types))

		p_number = ncapt(fr'one|two|three|four|five|six|seven|eight|nine|ten|\d+')
		cp_number = capt(fr'one|two|three|four|five|six|seven|eight|nine|ten|\d+', name='number')

		p_choice = ncapt(fr'(?: your choice of| any combination of)?')
		p_sep = ncapt(fr',? or,?|,? and,?|,? as well as|,') + p_choice
		cp_sep = capt(fr',? or,?|,? and,?|,? as well as|,', name='sep') + p_choice

		p_following = ncapt(fr'{p_number}(?: of)?(?: the)?(?: following {p_trait_types}(?: of your choice)?:)?')
		cp_following = ncapt(fr'{cp_number}(?: of)?(?: the)?(?: following {p_trait_types}(?: of your choice)?:)?')

		p_prepo = ncapt(fr'the(?: chosen)?|an?|that|these|{p_following}') + ncapt(fr'(?: set of)?')
		cp_prepo = ncapt(fr'the(?: chosen)?|an?|that|these|{cp_following}') + ncapt(fr'(?: set of)?')

		p_prefix1 = ncapt(fr'(?:have|gain|grants you) proficiency')
		p_prefix2 = ncapt(fr'(?:are|become) proficient')
		p_prefix = ncapt(fr'(?:{p_prefix1}|{p_prefix2}) (?:in|with)') + p_choice

		p_posfix = ncapt(fr'\(your choice\)|of your choice')

		p_1trait = ncapt(fr'(?:{p_prefix} )(?:{p_prepo} )?' + p_types["all"] + fr'(?: {p_posfix})?')
		p_trait = ncapt(fr'(?:{p_prefix} )?(?:{p_prepo} )?' + p_types["all"] + fr'(?: {p_posfix})?')
		cp_trait = ncapt(fr'(?:{p_prefix} )?(?:{cp_prepo} )?' + cp_types["all"] + fr'(?: {p_posfix})?')

		p_traits = ncapt(fr'{p_1trait if require_prefix else p_trait}(?:(?:{p_sep} {p_trait})*)')
		cp_traits = ncapt(fr'(?:{cp_sep} )?{cp_trait}(?P<rest>(?:{p_sep} {p_trait})*)')

		def process_group(group, mode):
			nonlocal choices, grants
			# print('processing group')
			# print(f'{group=}')
			# print(f'{mode=}')

			for t in group:
				if t["generic"]:
					if t["trait"] not in generic_types[t["trait_type"]] and getPlural(t["trait"]) in generic_types[t["trait_type"]]:
						t["trait"] = getPlural(t["trait"])
					cfg = generic_types[t["trait_type"]][t["trait"]]
					if "id" in cfg:
						if t["generic"] == 'all':
							if cfg["id"] == '*':
								t["disabled"] = True
								traits = [ {
									"trait_type": t["trait_type"],
									"trait": new_t["name"].lower(),
									"id": new_t["id"],
									"number": t["number"],
									"generic": False,
									"disabled": False,
								} for new_t in types[t["trait_type"]].values() ]
								traits = { trait["id"]: trait for trait in traits }.values()
								if mode == 'and':
									group += traits
								elif mode == 'or':
									raise ValueError('Multiple traits with generic=\'all\' on \'or\' mode', group, traits, mode, generic)
							elif cfg["id"].endswith(':*'): t["id"] = cfg["id"][:-2]
							else: t["id"] = cfg["id"]
						elif cfg["id"].endswith(':*'):
							if mode == 'or':
								t["id"] = cfg["id"]
							elif mode == 'and':
								process_group([t], 'or')
								t["disabled"] = True
						else:
							t["id"] = cfg["id"]
					else:
						t["disabled"] = True
						traits = []
						if "ids" in cfg:
							traits = [ {
								"trait_type": t["trait_type"],
								"trait": t["trait"],
								"id": t_id,
								"number": t["number"],
								"generic": False,
								"disabled": False,
							} for t_id in cfg["ids"] ]
						else:
							traits = [ {
								"trait_type": t["trait_type"],
								"trait": new_t["name"].lower(),
								"id": new_t["id"],
								"number": t["number"],
								"generic": False,
								"disabled": False,
							} for new_t in types[t["trait_type"]].values() if cfg["foo"](t["trait"], new_t) ]
							traits = { trait["id"]: trait for trait in traits }.values()

						if t["generic"] == 'all':
							for trait in traits:
								if trait["id"].endswith(':*'):
									trait["id"] = trait["id"][:-2]
							if mode == 'and':
								group += traits
							elif mode == 'or':
								raise ValueError('Multiple traits with generic=\'all\' on \'or\' mode', group, traits, mode, generic)
						else:
							if mode == 'or':
								group += traits
							elif mode == 'and':
								process_group(traits, 'or')
				elif not "id" in t:
					if t["trait"] in types[t["trait_type"]]:
						t["id"] = types[t["trait_type"]][t["trait"]]["id"]
					else:
						raise ValueError(t, group, mode)
				t["type_id"] = types_ids[t["trait_type"]]
				if not t["disabled"] and "id" not in t: raise ValueError(t, group, mode)

			number = ([ t["number"] for t in group if t["number"] ]+[1])[0]
			group = [ t for t in group if not t["disabled"] ]

			if mode == 'or':
				choices.append({
					"count": number or 1,
					"pool": [ f'{t["type_id"]}:{t["id"]}' for t in group ],
				})
			elif mode == 'and':
				grants.extend([ f'{t["type_id"]}:{t["id"]}' for t in group if not t["generic"] ])
				for t in group:
					if not t["generic"]: continue
					choices.append({
						"count": t["number"] or 1,
						"pool": [ f'{t["type_id"]}:{t["id"]}' ],
					})
			else:
				raise ValueError(mode, group, mode)

		def get_traits(match):
			subtext = match[0]
			current = []

			# print(f'{text=}')

			while subtext:
				submatch = re.search(cp_traits, f'{subtext}')
				if not submatch: break

				generic = False
				trait_type = [ t for t in types if submatch.groupdict().get(f'type_{t}') ]
				if len(trait_type):
					trait_type = trait_type[0]
					trait = submatch.groupdict().get(f'type_{trait_type}')
				else:
					trait_type = [ t for t in generic_types if submatch.groupdict().get(f'gtype_{t}') ][0]
					trait = submatch.groupdict().get(f'gtype_{trait_type}')
					generic = True

				number = toInt(submatch.groupdict().get('number') or '', allowWords=True, default=None)
				rest = submatch.groupdict().get('rest') or ''
				sep = submatch.groupdict().get('sep') or ''

				if generic and submatch.groupdict().get('all_'+trait_type): generic = 'all'

				mode = None
				if re.search(r'or', sep): mode = 'or'
				if re.search(r'and|as well as', sep): mode = 'and'

				# print(f'{subtext=}')
				# print(f'{number=} {trait=} {trait_type=} {sep=} {rest=} {mode=}')

				trait = {
					"trait_type": trait_type,
					"trait": trait,
					"number": number,
					"generic": generic,
					"disabled": False,
				}

				if mode == 'or':
					current.append(trait)
					process_group(current, 'or')
					current = []
				elif mode == 'and':
					process_group(current, 'and')
					current = []
					current.append(trait)
				else:
					current.append(trait)

				subtext = rest

			if len(current):
				process_group(current, 'and')

			return 'PROCESSED'
		text = re.sub(p_traits, get_traits, text)

		patterns = [
			r'someone proficient',
			r'must be proficient',
			r'double your proficiency',
			r'proficiency bonus',
			r'considered proficient',
			r'would already be proficient',
			r'choose a \w+( or \w+)? you are proficient with',
			r'not already proficient',
			r'choose to increase your level of proficiency in that check',
			r'from \w+ to proficient',
			r'from proficient to \w+',
			r'that you are proficient with',
			r'you are proficient with it',
			r'in which you are proficient',
			r'with which you are proficient',
			r'with which are you proficient',
			r'if you are proficient',
			r'if you are already proficient',
			r'using a \w+ you are proficient in',
			r'your beast gains proficiency',
			r'each creature gains proficiency',
			r'creature was already proficient',
			r'they instead become proficient',
			r'give (\w+ )?creatures (\w+ ){0,2}proficiency',
			r'retain this proficiency',
			r'are not proficient',
			r'proficient in initiative',
			r'must have proficiency',
			r'to gain proficiency in',
			r'you require proficiency',
			r'already have (this )?proficiency',
			r'lose your proficiency',
			r'treated as proficient',
			r'in place of the \w+ proficiency',
			r'in which you are granted proficiency',
			r'with proficiency',
			r'if \w+ gain \w+ proficiency',
			r'may add \w+ proficiency',
			r'proficiency from the above list',
			r'you are proficient in this weapon',
		]
		for pat in patterns: text = re.sub(pat, "PROCESSED", text)

		if re.search(f'proficient|proficiency', text):
			print('Unprocessed proficiency:', text, '\n', _text)
			a = b

	# if name == 'Anzellan' and (choices or grants): print(f'{choices=} {grants=}')

	return choices, grants

def lowerCase(word):
	return word[:1].lower() + word[1:]

def capitalCase(word):
	return word[:1].upper() + word[1:]

toIntDefault = {}
def toInt(string, allowWords=False, default=toIntDefault):
	if allowWords:
		numbers = [ "one", "two", "three", "four", "five", "six", "seven", "eigth", "nine", "ten" ]
		try:
			return numbers.index(string.lower()) + 1
		except ValueError:
			pass
	try:
		return int(string)
	except ValueError:
		if default != toIntDefault: return default
		else: return string

def getSingular(Text):
	possibilities = []
	text = Text.lower()
	if text in ('sheep', 'series', 'species', 'deer', ''): return [Text]
	if re.search('(s|ss|sh|ch|x|z|o)es$', text): possibilities.append(Text[:-2])
	if re.search('ies$', text): possibilities.append(Text[:-3]+'y')
	if re.search('ves$', text): possibilities.append(Text[:-3]+'f')
	if re.search('ves$', text): possibilities.append(Text[:-3]+'fe')
	if re.search('es$', text): possibilities.append(Text[:-2]+'is')
	if re.search('i$', text): possibilities.append(Text[:-1]+'us')
	if re.search('a$', text): possibilities.append(Text[:-1]+'on')
	if re.search('s$', text): possibilities.append(Text[:-1])
	return possibilities

def getPlural(Text):
	text = Text.lower()
	if text in ('sheep', 'series', 'species', 'deer'): return Text
	elif text.endswith('weapon'): return text+'s'
	elif re.search('[^aeiou]y$', text): return Text[:-1]+'ies'
	elif re.search('us$', text): return Text[:-2]+'i'
	elif re.search('is$', text): return Text[:-2]+'es'
	elif re.search('on$', text): return Text[:-2]+'a'
	elif re.search('(s|ss|sh|ch|x|z|o)$', text): return Text+'es'
	elif re.search('f$', text): return Text[:-1]+'ves'
	elif re.search('fe$', text): return Text[:-2]+'ves'
	return Text+'s'

def slugify(text, capitalized=True, space=''):
	if capitalized: text = re.sub(r'(\b\w+\b)', lambda w: w[0].capitalize(), text)
	else: text = text.lower()
	if space != '': text = text.strip()
	text = re.sub(r'[/,]', r'-', text)
	text = re.sub(r'[\s]+', space, text)
	text = re.sub(r'^\(([^)]*)\)', r'\1-', text)
	text = re.sub(r'-*\(([^)]*)\)', r'-\1', text)
	text = re.sub(fr'[^-\w{space}]', r'', text)
	return text

def toBase(number, base=10, alphabet=(string.digits+string.ascii_letters)):
	if (base < 2) or (base > len(alphabet)):
		raise AssertionError("int2base base out of range")
	if number < 0:
		return '-' + int2base(-number, base, alphabet)
	if type(number) == float:
		whole, frac = f'{number:.20f}'.split('.')
		return f'{toBase(int(whole), base, alphabet)}.{toBase(int(frac), base, alphabet)}'
	ans = ''
	while number:
		ans += alphabet[number % base]
		number //= base
	return ans[::-1] or '0'

def randomID(length=16):
	def rnd(): return toBase(random.random(), 62)[2:]
	ID = ''
	while len(ID) < length: ID += rnd()
	return ID[:length]
