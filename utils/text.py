import re, json

def cleanStr(string):
	if string:
		string = ' '.join(string.split(' ')) or ''
		string = re.sub(r'\ufffd', r'—', string) or ''
		string = re.sub(r'\r', r'', string) or ''
		string = re.sub(r'\n\n', r'\n', string) or ''
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
		return '\r\n'.join(lines)

def getAction(text, uses, recharge):
	src = text
	if text:
		if re.search(r'bonus action', src):
			return 'bonus'
		elif re.search(r'as an action|can take an action', src):
			return 'action'
		elif re.search(r'you can use your reaction|using your reaction|you can use this special reaction', src):
			return 'reaction'
		elif uses or (recharge != 'none'):
			return 'special'
		else:
			return 'none'
	return 'none'

def getUses(text, name):
	uses, recharge = 0, 'none'

	if text:
		patSR = r'(finish|finishes|complete) a short(?: rest)?(?: or(?: a)? long rest)'
		patSR += r'|regain all expended uses on a short(?: or long)? rest'
		patLR = r'(finish|finishes|complete) a long rest'
		patSR += r'|regain all expended uses on a long rest'
		patRC = r'until you move 0 feet on one of your turns'
		patRC += r'|until you store'

		isSR = re.search(patSR, text)
		isLR = (not isSR) and re.search(patLR, text)
		isRC = (not isSR) and (not isLR) and re.search(patRC, text)

		def ncapt(patt): return f'(?:{patt})'
		def capt(patt): return f'({patt})'

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

		pat_modifier = r'a (?:combined |maximum )?number of (?:power surges |(?P<times>times?) )?equal to (?:(?P<base>\d+) \+ )?(?P<half>half )?your '
		pat_modifier += r'(?P<ability1>Strength|Dexterity|Constitution|Intelligence|Wisdom|Charisma|Critical Analysis)'
		pat_modifier += r'(?: or (?P<ability2>Strength|Dexterity|Constitution|Intelligence|Wisdom|Charisma))? modifier'
		pat_modifier += r'(?: \((?:your choice, )?(?:rounded (?P<rounded>down|up) )?(?:a )?minimum of (?P<min>\d+|once)\))?'

		sp_n = r'one|two|three|four|five|six|seven|eight|nine|ten|\d+'
		sp_n_times = capt(sp_n) + r' times|(once|twice|thrice)'
		pat_number = r'[Yy]ou can ' + ncapt(sp_action) + r' (?:a (?:combined )?total of )?' + ncapt(sp_n_times)
		pat_number += r'|[Yy]ou have ' + capt(sp_n) + r' (?:superiority dice|amplified shots|(?:\w+ )?points)'

		pat_prof = r'a (?:combined )?number of times equal to (?P<half>half )?your proficiency bonus'
		pat_prof += r'|in excess of (?P<half2>half )?your proficiency bonus \(resetting on a long rest\)'

		pat_once = r'[Oo]nce you(?:[\'—]ve| have)? ' + ncapt(sp_action_past)
		pat_once += r'|[Yy]ou (?:can[\'—]t|cannot|can not) ' + ncapt(sp_action) + r' (?:again )?until'
		pat_once += r'|[Ii]f you ' + ncapt(sp_action) + r' again before'

		pat_custom = r'(?P<twiceScoutLevelPlusInt>That barrier has hit points equal to twice your scout level \+ your Intelligence modifier)'
		pat_custom += r'|(?P<twiceConsularLevelPlusWisOrCha>The barrier has hit points equal to twice your consular level \+ your Wisdom or Charisma modifier \(your choice\))'
		pat_custom += r'|(?P<fiveTimesEngineerLevel>has a number of hit points equal to 5 x your engineer level)'
		pat_custom += r'|(?P<moreUses>[Yy]ou have ' + ncapt(sp_n) + r' (?:superiority dice|amplified shots|(?:\w+ )?points), instead of)'
		pat_custom += r'|(?P<roll2d20>[Ww]hen you finish a long rest, roll two d20s)'
		pat_custom += r'|(?P<borrowedLuck>borrowed luck roll)'
		pat_custom += r'|(?P<powercasting>[Yy]ou regain all expended (?:force|tech) points when you)'
		pat_custom += r'|(?P<limitPerTarget>you can[\'—]t use this feature on them again until|they (?:cannot|can not|can[\'—]t) do so again until|creature can[\'—]t (?:regain hit points|receive it) again (?:in this way )?until)'
		pat_custom += r'|(?P<quickThinking>You regain all of your expended uses of Potent Aptitude when you finish a short or long rest)'
		pat_custom += r'|(?P<rage>You can enter a rage a number of times)'
		pat_custom += r'|(?P<focusPoints>Your monk level determines the number of points you have)'
		pat_custom += r'|(?P<increasingDC>use this feature after the first, the DC)'
		pat_custom += r'|(?P<lastsUntilRest>it lasts until you (?:complete|finish))'
		pat_custom += r'|(?P<chooseOnRest>rest, you can (?:choose|replace))'

		m_mod = re.search(pat_modifier, text)
		m_number = re.search(pat_number, text)
		m_prof = re.search(pat_prof, text)
		m_once = re.search(pat_once, text)
		m_custom = re.search(pat_custom, text)
		if m_mod:
			# print(f'{m_mod.group(0)=}')
			# print(f'{m_mod.groups()=}')

			if m_mod.group('times') == 'time':
				print(f'		Possible typo detected on {name}, count using "time" instead of "times"')

			uses_ability1 = m_mod.group('ability1') or ''
			uses_ability2 = m_mod.group('ability2') or ''
			if uses_ability1 == 'Critical Analysis': uses_ability1 = 'int'
			else: uses_ability1 = uses_ability1[:3].lower()
			if uses_ability2: uses_ability2 = uses_ability2[:3].lower()

			uses_base = int(m_mod.group('base') or 0)
			uses_half = m_mod.group('half')
			uses_rounded = m_mod.group('rounded')
			uses_min = 1 if m_mod.group('min') == 'once' else int(m_mod.group('min') or 0)

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
		elif m_number:
			number = m_number.group(1) or m_number.group(2) or m_number.group(3)
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
		elif m_prof:
			uses = '@details.prof'
			if m_prof.group('half') or m_prof.group('half2'): uses = f'floor({uses}/2)'
		elif m_once:
			uses = 1
		if m_custom:
			if m_custom.group('twiceScoutLevelPlusInt'):
				uses = '2 * @classes.scout.levels + floor((@abilities.int.score - 10) / 2)'
				#TODO: Change this when foundry supports ability mod on max uses
				# uses = '2 * @classes.scout.levels + @abilities.int.mod'
			if m_custom.group('twiceConsularLevelPlusWisOrCha'):
				uses = '2 * @classes.consular.levels + floor((max(@abilities.wis.score, @abilities.cha.score) - 10) / 2)'
				#TODO: Change this when foundry supports ability mod on max uses
				# uses = '2 * @classes.consular.levels + max(@abilities.wis.mod, @abilities.cha.mod)'
			if m_custom.group('fiveTimesEngineerLevel'):
				uses = '5 * @classes.engineer.levels'
			elif m_custom.group('rage'):
				lvl = '@classes.berserker.levels'
				uses = f'{lvl} < 3 ? 2 : {lvl} < 6 ? 3 : {lvl} < 12 ? 4 : {lvl} < 17 ? 5 : {lvl} < 20 ? 6 : 999'
			elif m_custom.group('focusPoints'):
				uses = '@classes.monk.levels'
			elif m_custom.group('borrowedLuck') or \
				m_custom.group('powercasting') or \
				m_custom.group('limitPerTarget') or \
				m_custom.group('increasingDC') or \
				m_custom.group('quickThinking') or \
				m_custom.group('lastsUntilRest') or \
				m_custom.group('roll2d20') or \
				m_custom.group('moreUses') or \
				m_custom.group('chooseOnRest'):
				isSR, isLR, isRC, uses = False, False, False, 0

		if (isSR or isLR or isRC) and not (m_mod or m_number or m_prof or m_once or m_custom):
			pat_modifier = re.sub(r'\(\?P<\w+>', r'\(', pat_modifier)
			print(f'{pat_modifier=}\n')
			pat_number = re.sub(r'\(\?P<\w+>', r'\(', pat_number)
			print(f'{pat_number=}\n')
			pat_prof = re.sub(r'\(\?P<\w+>', r'\(', pat_prof)
			print(f'{pat_prof=}\n')
			pat_once = re.sub(r'\(\?P<\w+>', r'\(', pat_once)
			print(f'{pat_once=}\n')
			pat_custom = re.sub(r'\(\?P<\w+>', r'\(', pat_custom)
			print(f'{pat_custom=}\n')
			print(f'Failed to recognize uses count: on {name}')
			# print(f'{=}')
			for line in text.split('\n'):
				print(line)
			print('\n')
			x = exitaaa
		if uses and not (isSR or isLR or isRC):
			print(f'Recognized {uses=}, but failed to recognize recharge on {name}')
			# print(f'{=}')
			for line in text.split('\n'):
				print(line)
			print('\n')
			x = exitaaa
		if (isSR and isSR.group(1) == 'finishes') or (isLR and isLR.group(1) == 'finishes'):
			print(f'		Possible typo detected on {name}, recharge using "finishes" instead of "finish"')

		if isSR: recharge = 'sr'
		if isLR: recharge = 'lr'
		if isRC: recharge = 'charges'

	return uses, recharge

def raw(raw_item, attr):
	return raw_item[attr] if (attr and attr in raw_item) else None

def clean(raw_item, attr, default=''):
	item = raw(raw_item, attr) or default
	return cleanStr(item)

def cleanJson(raw_item, attr):
	item = clean(raw_item, attr+'Json', default='[]')
	return json.loads(item)

def getProperty(prop_name, props):
	if prop_name not in props: return None

	def opt(p): return f'(?:{p})?'
	def capt(p, name): return f'(?P<{name}>{p})'

	prop = props[prop_name]

	if re.search('special', prop): return 'special'

	it = re.finditer(r'(\d+(?:,\d+)?)|(\d+d\d+)', prop)
	vals = [int(re.sub(',', '', val.group(1))) or val.group(2) for val in it]
	if len(vals) == 0: return True
	if len(vals) == 1: return vals[0]
	return vals
