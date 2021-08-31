import sw5e.sw5e
import re

class Feature(sw5e.sw5e.Item):
	def __init__(self, raw_item, old_item, importer):
		super().__init__(raw_item, old_item, importer)

		def raw(attr): return attr and raw_item[attr]
		def clean(attr): return attr and self.cleanStr(raw_item[attr])
		def cleanJson(attr): return attr and (clean(attr+"Json") or '  ')[2:-2].split('","')

		self.text = clean("text")
		self.level = raw("level")
		self.sourceEnum = raw("sourceEnum")
		self.source = clean("source")
		self.sourceName = clean("sourceName")
		self.metadata = raw("metadata")
		self.partitionKey = clean("partitionKey")
		self.rowKey = clean("rowKey")

		#TODO: Remove this once the typo is fixed
		if self.sourceName == 'Juyo/Vapaad Form': self.sourceName = 'Juyo/Vaapad Form'

		self.type = "classfeature" if self.source in ["Class", "Archetype"] else "feat"
		self.content_source = self.getContentSource(importer)
		self.class_name = self.getClassName(importer)
		self.action = self.getAction()
		self.uses, self.recharge = self.getUses()

	def getClassName(self, importer):
		if self.source == 'Archetype':
			archetype = importer.get('archetype', name=self.sourceName)
			if archetype:
				return archetype.className
			else:
				self.brokenLinks = True
				return ''
		elif self.source == 'Class':
			return self.sourceName

	def getAction(self):
		src = self.text
		if re.search(r'bonus action', src):
			return 'bonus'
		elif re.search(r'as an action|can take an action', src):
			return 'action'
		elif re.search(r'you can use your reaction|using your reaction|you can use this special reaction', src):
			return 'reaction'
		elif re.search(r'you can\'t use this feature again|once you use this feature|legendary resistance', src):
			return 'special'
		else:
			return 'none'

	def getImg(self):
		if self.source in ['Class', 'Archetype']:
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
			}[self.class_name] or 'BSKR'
			action = {
				'bonus': 'Bonus',
				'action': 'Action',
				'reaction': 'Reaction',
				'special': 'Action',
				'none': 'Passive'
			}[self.action] or 'Passive'
			return f'systems/sw5e/packs/Icons/Class%20Features/{class_abbr}{"-ARCH" if self.source == "Archetype" else ""}-{action}.webp'
		else:
			name = self.sourceName
			name = re.sub(r'[ /]', r'%20', name)
			return f'systems/sw5e/packs/Icons/Species/{name}.webp'

	def getUses(self):
		uses, recharge = 0, 'none'

		patSR = r'(finish|complete) a short( rest)?( or( a)? long rest)'
		patSR += r'|regain all expended uses on a short(?: or long)? rest'
		patLR = r'(finish|complete) a long rest'
		patSR += r'|regain all expended uses on a long rest'
		patRC = r'until you move 0 feet on one of your turns'

		isSR = re.search(patSR, self.text)
		isLR = (not isSR) and re.search(patLR, self.text)
		isRC = (not isSR) and (not isLR) and re.search(patRC, self.text)

		pat_modifier = r'a (?:combined |maximum )?number of (?:power surges |(?P<times>times?) )?equal to (?:(?P<base>\d+) \+ )?(?P<half>half )?your (?P<ability1>Strength|Dexterity|Constitution|Intelligence|Wisdom|Charisma|Critical Analysis)(?: or (?P<ability2>Strength|Dexterity|Constitution|Intelligence|Wisdom|Charisma))? modifier(?: \((?:your choice, )?(?:rounded (?P<rounded>down|up) )?(?:a )?minimum of (?P<min>\d+|once)\))?'
		pat_number = r'[Yy]ou can (?:use (?:this|each) feature|initiate playing an enhanced song|invoke each of your totems) (once|twice|thrice)|[Yy]ou can use this feature (one|two|three|four|five|six|seven|eight|nine|ten) times|[Yy]ou have (one|two|three|four|five|six|seven|eight|nine|ten) (?:superiority dice|amplified shots), which'
		pat_prof = r'a (:?combined )?number of times equal to (?P<half>half )?your proficiency bonus|in excess of (?P<half2>half )?your proficiency bonus \(resetting on a long rest\)'
		pat_once = r'[Oo]nce you(?:\'ve| have)? (?:do(?:ne)? so|invoked? a totem in this way|created? a panacea|used? (?:it|(?:this|the chosen) (?:feature|trait)))'
		pat_once += r'|[Yy]ou (?:can\'t|cannot|can not) (?:do so|invoke it|create another|use (?:it|(?:this|the chosen) (?:feature|trait))) (?:again )?until'
		pat_once += r'|[Ii]f you use (?:it|this|the chosen) (?:feature|trait) again before'
		pat_twice = r'[Yy]ou can manifest your ideals a combined total of twice|[Ww]hen you finish a long rest, roll two d20s'
		pat_custom = r'(?P<twiceScoutLevelPlusInt>That barrier has hit points equal to twice your scout level \+ your Intelligence modifier)|(?P<borrowedLuck>borrowed luck roll)|(?P<powercasting>[Yy]ou regain all expended (?:force|tech) points when you)|(?P<limitPerTarget>you can\'t use this feature on them again until|they (?:cannot|can not|can\'t) do so again until)|(?P<rage>You can enter a rage a number of times)|(?P<increasingDC>use this feature after the first, the DC)|(?P<quickThinking>You regain all of your expended uses of Potent Aptitude when you finish a short or long rest)|(?P<focusPoints>Your monk level determines the number of points you have)|(?P<lastsUntilRest>it lasts until you (?:complete|finish))|(?P<fiveTimesEngineerLevel>has a number of hit points equal to 5 x your engineer level)|(?P<chooseOnRest>rest, you can choose)|(?P<twiceConsularLevelPlusWisOrCha>The barrier has hit points equal to twice your consular level \+ your Wisdom or Charisma modifier \(your choice\))'

		m_mod = re.search(pat_modifier, self.text)
		m_number = re.search(pat_number, self.text)
		m_prof = re.search(pat_prof, self.text)
		m_once = re.search(pat_once, self.text)
		m_twice = re.search(pat_twice, self.text)
		m_custom = re.search(pat_custom, self.text)
		if m_mod:
			# print(f'{m_mod.group(0)=}')
			# print(f'{m_mod.groups()=}')

			if m_mod.group('times') == 'time':
				print(f'Typo detected on {self.name}, feature count using "time" instead of "times"')

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
				'ten': 10,
			}[m_number.group(1) or m_number.group(2) or m_number.group(3)]
		elif m_prof:
			uses = '@details.prof'
			if m_prof.group('half') or m_prof.group('half2'): uses = f'floor({uses}/2)'
		elif m_once:
			uses = 1
		elif m_twice:
			uses = 2
		elif m_custom:
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
				m_custom.group('chooseOnRest'):
				isSR, isLR, isRC, uses = False, False, False, 0
		elif isSR or isLR:
			print(f'Failed to recognize uses count: on {self.name}')
			# print(f'{=}')
			for line in self.text.split('\n'):
				print(line)
			print('\n')
			x = exitaaa
		if uses and not (isSR or isLR or isRC):
			print(f'Recognized {uses=}, but failed to recognize recharge on {self.name}')
			# print(f'{=}')
			for line in self.text.split('\n'):
				print(line)
			print('\n')
			x = exitaaa

		if isSR: recharge = 'sr'
		if isLR: recharge = 'lr'
		if isRC: recharge = 'charges'

		return uses, recharge

	def getRequirements(self):
		if self.level and self.level > 1: return f'{self.class_name} {self.level}'
		return self.sourceName

	def getContentSource(self, importer):
		sourceItem = importer.get(self.source.lower(), name=self.sourceName)
		if sourceItem:
			return sourceItem.contentSource
		else:
			self.brokenLinks = True
			return ''

	def getData(self, importer):
		data = super().getData(importer)
		data["type"] = self.type
		data["img"] = self.getImg()

		data["data"] = {}
		data["data"]["description"] = { "value": self.markdownToHtml(self.text) }
		data["data"]["requirements"] = self.getRequirements()
		data["data"]["source"] = self.content_source

		if self.action != 'none':
			data["data"]["activation"] = {
				"type": self.action,
				"cost": 1
			}

		#TODO: extract duration, target, range, uses, consume, damage and other rolls
		data["data"]["duration"] = {}
		data["data"]["target"] = {}
		data["data"]["range"] = {}
		data["data"]["uses"] = {
			"value": 0,
			"max": self.uses,
			"recharge": self.recharge
		}
		data["data"]["consume"] = {}
		data["data"]["ability"] = ''
		data["data"]["actionType"] = ''
		data["data"]["attackBonus"] = 0
		data["data"]["chatFlavor"] = ''
		data["data"]["critical"] = None
		data["data"]["damage"] = {
			"parts": [],
			"versatile": '',
		}
		data["data"]["formula"] = ''
		data["data"]["save"] = {}
		data["data"]["recharge"] = ''
		data["data"]["className"] = self.class_name

		return data

	def matches(self, *args, **kwargs):
		if not super().matches(*args, **kwargs): return False

		if len(args) >= 1:
			new_item = args[0]
			if new_item["level"] != self.level: return False
			if new_item["source"] != self.source: return False
			if new_item["sourceName"] != self.sourceName: return False

		return True
