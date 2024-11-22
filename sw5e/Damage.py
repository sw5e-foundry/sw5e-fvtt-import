import re

class Damage():
	default = {
		'custom': None,
		'number': None,
		'denomination': None,
		'bonus': None,
		'types': [],
		'scaling_mode': 'whole',
		'scaling_number': 1,
		'scaling_formula': None,
	}

	def __init__(self, validate=True, **kwargs):
		for key, val in self.default.items():
			if key in kwargs: setattr(self, key, kwargs[key])
			else: setattr(self, key, val)
		if validate and not self.valid():
			raise ValueError('Damage Data needs a denomination', kwargs)

	@classmethod
	def fromOldFormat(cls, old_part, validate=True):
		kwargs = {}
		main_pattern = r'(?P<number>\d*)d(?P<denom>\d+)'
		bonus_pattern = r'\s*(?:\+|\-)?\s*(?:\d+|@(?:\.?\w+)*)'
		full_pattern = fr'{main_pattern}(?P<bonus>(?:{bonus_pattern})+)?'
		if match := re.match(full_pattern, old_part[0]):
			kwargs['number'] = match.group('number') or 1
			kwargs['denomination'] = match.group('denom')
			kwargs['bonus'] = match.group('bonus')
		else:
			kwargs['custom'] = old_part[0]
		if len(old_part) == 2:
			kwargs['types'] = [old_part[1]]

		return Damage(validate=validate, **kwargs)

	def getData(self):
		return {
			"custom": {
				"enabled": self.custom != None,
				"formula": self.custom,
			},
			"number": self.number,
			"denomination": self.denomination,
			"bonus": self.bonus,
			"types": self.types,
			"scaling": {
				"mode": self.scaling_mode,
				"number": self.scaling_number,
				"formula": self.scaling_formula,
			}
		}

	def __repr__(self):
		return repr(self.repr())

	def repr(self, level=None):
		# TODO: scaling
		return self.custom or (f'{self.number}d{self.denomination}' + (f' + {self.bonus}' if self.bonus else ''))

	def valid(self):
		return not (self.denomination == None and self.custom == None)

class DamageGroup():
	def __init__(self, parts, allow_critical=True, validate=True):
		self.allow_critical = allow_critical
		self.parts = [ part if isinstance(part, Damage) else Damage(part, validate=validate) for part in parts ]

	@classmethod
	def fromOldFormat(cls, parts, allow_critical=True, validate=True):
		return DamageGroup([ Damage.fromOldFormat(part, validate=validate) for part in parts ], allow_critical=allow_critical)

	def getData(self):
		return {
			"critical": {
				"allow": self.allow_critical,
			},
			"parts": [ damage.getData() for damage in self.parts ]
		}

	def splitTypes(self, types, validate=True):
		types = set(types)
		no = [ part for part in self.parts if not len(types.intersection(part.types)) ]
		yes = [ part for part in self.parts if len(types.intersection(part.types)) ]
		no = DamageGroup(no, allow_critical=self.allow_critical, validate=validate)
		yes = DamageGroup(yes, allow_critical=self.allow_critical, validate=validate)
		return no, yes

	def __repr__(self):
		return repr(self.repr())

	def repr(self, level=0):
		return [ part.repr(level=level) for part in self.parts ]

#