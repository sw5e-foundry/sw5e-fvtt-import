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

			## Add inline rolls
			lines[i] = re.sub(r'\b((?:\d*d)?\d+\s*)x(\s*\d+)\b', r'\1*\2', lines[i])
			lines[i] = re.sub(r'\b(\d*d\d+(?:\s*[+*]\s*\d+)?)\b', r'[[/r \1]]', lines[i])
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
		elif uses or recharge:
			return 'special'
	return None

def getUses(text, name):
	uses, recharge = None, None

	found = False

	if text:
		text = text.lower()

		patSR = r'(finish|finishes|complete|after) a short(?: rest)?(?: or(?: a)? long rest)'
		patSR += r'|regains? all expended (?:uses|charges) (?:on|after) a short(?: or long)? rest'
		patLR = r'(finish|finishes|complete) a long rest'
		patLR += r'|regains? all expended (?:uses|charges) (?:on|after) a long rest'
		patRC = r'until you move 0 feet on one of your turns'
		patRC += r'|until you (?:store|reload|recover)'

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
					else:
						uses = f'floor(({uses})/2)'

		if not found: ## PROF times
			pattern = r'a (?:combined )?number of (?:times|charges|superiority dice|force points in this way) equal to (?P<half>half )?your proficiency bonus'
			pattern += r'|in excess of (?P<half2>half )?your proficiency bonus \(resetting on a long rest\)'

			if match := re.search(pattern, text):
				found = True

				uses = '@attributes.prof'
				if match['half'] or match['half2']:
					uses = f'floor({uses}/2)'

		if not found: ## CLASS LEVEL times
			pattern = r'a (?:combined )?number of (?:times|charges) equal to (?P<half>half )?your (?P<class>\w+) level(?: \(rounded (?P<round>up|down)\))?'

			if match := re.search(pattern, text):
				found = True

				uses = f'@classes.{match["class"].lower()}.levels'
				if match['half']:
					if match['round'] == 'up':
						uses = f'ceil({uses}/2)'
					else:
						uses = f'floor({uses}/2)'

		sp_action = r'use (?:it|(?:this|each|the chosen) (?:feature|trait|ability))'
		sp_action += r'|initiate playing an enhanced song'
		sp_action += r'|invoke each of your totems'
		sp_action += r'|invoke a totem this way'
		sp_action += r'|create a panacea'
		sp_action += r'|manifest your ideals'
		sp_action += r'|(?:cast|do) (?:it|so)'
		sp_action += r'|activate'

		sp_action_past = r'used? (?:it|(?:this|each|the chosen) (?:feature|trait|ability))'
		sp_action_past += r'|initiated? playing an enhanced song'
		sp_action_past += r'|invoked? each of your totems'
		sp_action_past += r'|invoked? a totem this way'
		sp_action_past += r'|created? a panacea'
		sp_action_past += r'|manifest(?:ed)? your ideals'
		sp_action_past += r'|(?:cast|do(?:ne)?) (?:it|so)'
		sp_action_past += r'|activated?'

		sp_n = r'one|two|three|four|five|six|seven|eight|nine|ten|\d+'
		sp_n_times = capt(sp_n) + r' times|(once|twice|thrice)'

		if not found: ## NUMBER times
			pattern = fr'you (?:can|may) {ncapt(sp_action)} (?:a (?:combined )?total of )?{ncapt(sp_n_times)}'
			pattern += fr'|(?:you have|(?:this|the) \w+ has) {capt(sp_n)} (?:superiority dice|amplified shots|(?!hit)(?:\w+ )?points|charges)'

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
			pattern += r'|rest, you can (?:choose|replace|change)'
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

		pattern = r'choose one(?P<type>hostile |allied)?\s+creature'
		if match := re.search(pattern, text):
			if match['type'] == 'hostile': return 1, '', 'enemy'
			elif match['type'] == 'allied': return 1, '', 'ally'
			else: return 1, '', 'creature'

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

def getRange(text, name):
	pattern = r'within (?P<value>\d+) (?P<unit>\w+)'
	if match := re.search(pattern, text):
		return match["value"], match["unit"]

	return None, ''

def getAction(text, name, scale=None):
	action_type, damage, formula, save, save_dc, scaling = '', { "parts": [], "versatile": '' }, '', '', None, { "mode": 'none'}

	if text:
		text = text.lower()

		## Power Attack
		pattern = r'(make|making) a (?P<range>ranged|melee) (force|tech) attack'
		if (match := re.search(pattern, text)):
			if match['range'] == 'ranged': action_type = 'rpak'
			else: action_type = 'mpak'

		## Saving Throw
		sp_ability = r'strength|dexterity|constitution|intelligence|wisdom|charisma'
		pattern = r'(?:succeed on|make|makes|if it fails) an? (dc (?P<dc>\d+) )?'
		pattern += fr'(?P<save1>{sp_ability})(?: or (?P<save2>{sp_ability}))? saving throw'
		if (match := re.search(pattern, text)):
			action_type = action_type or 'save'
			#TODO find a way to use save1 or save2
			save = match['save1'][:3].lower()
			save_dc = int(match["dc"]) if match["dc"] else None

		## Dice formula
		p_formula = r'(?P<dice>\d*d\d+(?:\s*\+\s*\d*d\d+)*)?(?:(?:\s*\+\s*)?(?P<flat>\d+))?(?:\s*\+ your(?P<ability_mod> [\w ]+?)(?: ability)? modifier)?'
		p_dformula = r'(?P<dice>\d*d\d+(?:\s*\+\s*\d*d\d+)*)(?:(?:\s*\+\s*)?(?P<flat>\d+))?(?:\s*\+ your(?P<ability_mod> [\w ]+?)(?: ability)? modifier)?'

		## Healing
		pattern = fr'(?:(?:(?:re)?gains?|restores|gaining|a number of) (?P<temp>temporary )?hit points equal to |hit points increase by ){p_formula}'
		pattern2 = fr'(?:(?:re)?gains?|restores?|gaining) (?:an extra )?{p_formula} (?:extra |additional )?(?P<temp>temporary )?hit points'
		def foo(match):
			nonlocal action_type
			nonlocal damage
			dice, flat, ability_mod, temp = match.group('dice', 'flat', 'ability_mod', 'temp')

			if dice or flat or ability_mod:
				action_type = action_type or 'heal'
				formula = ('1'+dice if (dice.startswith('d')) else dice) if dice else None
				if flat:
					if formula: formula = f'{formula} + {flat}'
					else: formula = flat
				if ability_mod in ('strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma'):
					formula = f'{formula or ""} + @abilities.{ability_mod[:3]}.mod'
				elif ability_mod:
					formula = f'{formula or ""} + @mod'
				damage["parts"].append([ formula, 'temphp' if temp else 'healing' ])
				return 'FORMULA'
			else:
				return match.group(0)
		text = re.sub(pattern, foo, text)
		text = re.sub(pattern2, foo, text)

		## Damage
		pattern = fr'(?:(?:takes?|taking|deals?|dealing|do) (?:(?:an )?(?:extra|additional) |up to )?|, | (?:and|plus) (?:another |an extra )?)(?:damage equal to )?{p_formula}(?: of)?(?: (?P<type>\w+)(?:, (?:or )?\w+)*)?(?: damage|(?= [^.]+ damage))'
		pattern2 = fr'(?:the (?P<type>\w+ )?damage (?:also )?increases by|increase the damage by|(?:base|the additional|the extra) damage is|damage die becomes a) {p_formula}'
		def foo(match):
			nonlocal action_type
			nonlocal damage
			dice, flat, ability_mod = match.group('dice', 'flat', 'ability_mod')
			dmg_type = match.group('type') or '' if 'type' in match.groupdict() else ''

			if dice or flat or ability_mod:
				action_type = action_type or 'other'
				formula = ('1'+dice if (dice.startswith('d')) else dice) if dice else None
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
		pattern = fr'otherwise, it takes {p_dformula}'
		if (match := re.search(pattern, text)):
			dice, flat, ability_mod = match.group('dice', 'flat', 'ability_mod')

			formula = ('1'+dice if (dice.startswith('d')) else dice) if dice else None
			if flat:
				if formula: formula = f'{formula} + {flat}'
				else: formula = flat
			if ability_mod:
				formula = f'{(formula + " + ") or ""}@mod'
			damage["versatile"] = formula
		text = re.sub(pattern, r'FORMULA', text)

		## Other dice
		pattern = fr'(?:roll(?:ing)?(?: a| two)?|choose to add|(?:(?:is|are) (?:reduced|increased)|(?:increases|reduces) their current(?: and maximum)? \w+ points) by(?: an amount equal to)?|which are|die(?:, a)?) (?:an additional )?{p_dformula}(?<! )'
		pattern2 = fr'for {p_dformula} turns'
		pattern3 = fr'a {p_dformula} that you can roll'
		text = re.sub(pattern, foo, text)
		text = re.sub(pattern2, foo, text)
		text = re.sub(pattern3, foo, text)

		## Check for unprocessed dice
		pattern = r'\d*d\d+'
		def foo(match):
			nonlocal text
			nonlocal name

			dice = match[0]

			pattern_ignore = r'on the d20|d20 roll|rolls? the d20|roll of the d20|d20s'
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

			pattern_recognize = fr'{dice}(?: tiny projectiles| such fissures|(?:\s*x\s*\d+\s+)?feet)'
			pattern_recognize += fr'|\|\s*{dice}\s*\|'
			pattern_recognize += fr'|for {dice} days'


			formula = ('1'+dice if (dice.startswith('d')) else dice) if dice else None

			if re.search(pattern_ignore, text):
				return formula
			elif re.search(pattern_recognize, text):
				damage["parts"].append([ formula, '' ])
			else:
				raise ValueError(f'Unprocessed dice {formula} in {name}', text)

			return 'FORMULA'
		re.sub(pattern, foo, text)

		action_type = action_type or 'other'

	if scale:
		scaling["mode"] = "level" if re.search(r'Force Potency|Overcharge Tech', scale) else "atwill"

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

		#TODO: support regular power scaling


	return action_type, damage, formula, save, save_dc, scaling

def getDuration(text, name):
	if text:
		text = text.lower()

		sp_units = r'(?P<unit>minute|hour|day|month|year|turn|round)s?'

		## "lasts for 1 minute"
		## "lasts for 8 hours"
		pattern = fr'(?:^|\W)lasts (?:for )?(?:(?P<val>\d+) )?{sp_units}(?:\W|$)'
		if match := re.search(pattern, text):
			return match['val'] or 1, match['unit']

		## "for the next 8 hours"
		pattern = fr'(?:^|\W)for the next (?:(?P<val>\d+) )?{sp_units}(?:\W|$)'
		if match := re.search(pattern, text):
			return match['val'] or 1, match['unit']

		## "turned for 1 minute" (e.g. channel divinity)
		pattern = fr'(?:^|\W)turned for (?:(?P<val>\d+) )?{sp_units}(?:\W|$)'
		if match := re.search(pattern, text):
			return match['val'] or 1, match['unit']

		## "it is charmed by you for 1 minute"
		pattern = fr'(?:^|\W)is \w+ by you for (?:(?P<val>\d+) )?{sp_units}(?:\W|$)'
		if match := re.search(pattern, text):
			return match['val'] or 1, match['unit']

		## "once within the next 10 minutes"
		pattern = fr'(?:^|\W)once (?:with)?in the next (?:(?P<val>\d+) )?{sp_units}(?:\W|$)'
		if match := re.search(pattern, text):
			return match['val'] or 1, match['unit']

		## "For one minute"
		pattern = fr'(?:^|\W)for one {sp_units}(?:\W|$)'
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

def cleanJson(raw_item, attr, default='{}'):
	item = clean(raw_item, attr+'Json', default=default)
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

	it = re.finditer(r'(\d+d\d+)|(\d+(?:,\d+)?)', prop)
	vals = [val[1] or int(re.sub(',', '', val[2])) for val in it]
	if len(vals) == 0: return True
	if len(vals) == 1: return vals[0]
	return vals

def getProperties(targets, props_list, strict=False, error=False, needs_end=False):
	if not targets: return {}
	if type(targets) == str: targets = (targets,)

	pname_pat = fr'(?:{"|".join(props_list)})'
	if not strict: pname_pat = fr'(?:{"|".join(props_list).lower()})'
	pval_pat = r'(?: (?:\d+)| \((?:[^()]+)\))?'
	pval_pat_ = r'(?: (?P<flat>\d+)| \((?P<values>[^()]+)\))?'
	prop_pat = fr'(?:{pname_pat}(?=\W|$){pval_pat})'
	props_pat = fr'(?:{prop_pat}(?:, {prop_pat})*(?: and {prop_pat})?)'

	pattern = fr'(?P<neg>removes the )?(?P<props>{props_pat})(?: propert(?:y|ies))'
	if not needs_end: pattern += '?'
	properties = {}

	for target in targets:
		if not strict: target = target.lower()
		if re.search(pattern, target):
			for match in re.finditer(pattern, target):
				for prop in props_list:
					if not strict: prop = prop.lower()
					if (match2 := re.search(fr'{prop}(?=\W|$){pval_pat_}', match['props'])):
						if match['neg']:
							properties[prop] = False
						else:
							if match2['flat']:
								properties[prop] = int(match2['flat'])
							elif match2['values']:
								properties[prop] = match2['values']
							else:
								properties[prop] = True
		elif error:
			raise ValueError(props_list, target, targets)
	return properties

def lowerCase(word):
	return word[:1].lower() + word[1:]

def toInt(string):
	try:
		return int(string)
	except ValueError:
		return string

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

def getPlural(Text):
	text = Text.lower()
	if text in ('sheep', 'series', 'species', 'deer'): return Text
	elif re.search('[^aeiou]y$', text): return Text[:-1]+'ies'
	elif re.search('us$', text): return Text[:-2]+'i'
	elif re.search('is$', text): return Text[:-2]+'es'
	elif re.search('on$', text): return Text[:-2]+'a'
	elif re.search('(s|ss|sh|ch|x|z|o)$', text): return Text+'es'
	elif re.search('f$', text): return Text[:-1]+'ves'
	elif re.search('fe$', text): return Text[:-2]+'ves'
	return Text+'s'
