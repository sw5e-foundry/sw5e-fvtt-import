import utils.text
import re, json

class Advancement():
	def getType(self):
		return self.__class__.__name__
	def getData(self, importer):
		data = {
			"_id": utils.text.randomID(),
			"type": self.getType(),
			"configuration": {},
			"value": {},
		}
		return data

class AbilityScoreImprovement(Advancement):
	def __init__(self, name=None, points=2, fixed=[], level=1, class_restriction=""):
		self.name = name
		self.configuration = {
			"fixed": fixed,
			"points": points
		}
		self.level = level
		self.class_restriction = class_restriction

	def getData(self, importer):
		data = super().getData(importer)

		data["configuration"] = self.configuration
		data["level"] = self.level
		if self.name: data["title"] = self.name
		data["classRestriction"] = self.class_restriction

		return data

class HitPoints(Advancement):
	pass

class ScaleValue(Advancement):
	def __init__(self, name="Scale Value", values={}):
		self.name = name
		values, value_type, distance = self.processValues(values)
		self.configuration = {
			"identifier": utils.text.slugify(name, capitalized=False, space='-'),
			"scale": values,
			"type": value_type,
		}
		if distance: self.configuration["distance"] = { "units": distance }

	def processValues(self, raw_values):
		values = { lvl: str(raw_values[lvl]) for lvl in range(1, 21) if lvl in raw_values and raw_values[lvl] != '—' }
		value_type = ''
		distance = None

		if all(re.fullmatch(r'[+-]?\d+|Unlimited', n) for n in values.values()):
			value_type = 'number'
			values = {
				lvl: {
					"value":
						value[1:] if value.startswith('+') else
						10000 if value == 'Unlimited' else
						int(value)
				} for lvl, value in values.items()
			}
			# Remove leading zeroes
			non_zero = [ lvl for lvl in range(1, 21) if values.get(lvl, 0) != 0 ]
			if len(non_zero): values = { lvl: value for lvl, value in values.items() if lvl >= non_zero[0] }
		elif all(re.fullmatch(r'\d*d\d+', n) for n in values.values()):
			value_type = 'dice'
			values = {
				lvl: re.search(r'(?P<n>\d*)d(?P<die>\d+)', value).groupdict()
				for lvl, value in values.items()
			}
			values = {
				lvl: {
					"n": int(value["n"] or 1),
					"die": int(value["die"]),
				} for lvl, value in values.items()
			}
		elif all(re.fullmatch(r'[+-]?\d+ (?:ft|mi|m|km)\.', n) for n in values.values()):
			value_type = 'distance'
			for value in values.values():
				if match := re.fullmatch(r'[+-]?\d+ (?P<unit>ft|mi|m|km)\.', value):
					distance = match['unit']
					break

			values = {
				lvl: {
					"value": int(re.search(r'-?\d+', value).group(0))
				} for lvl, value in values.items()
			}
		else:
			value_type = 'string'
			values = {
				lvl: { "value": value }
				for lvl, value in values.items()
			}

		# Remove consecutive duplicates
		values = { lvl: value for lvl, value in values.items() if (value != values.get(lvl-1)) }

		return values, value_type, distance

	def getData(self, importer):
		data = super().getData(importer)

		data["configuration"] = self.configuration
		data["title"] = self.name

		return data

class ItemGrant(Advancement):
	def __init__(self, name=None, uids=[], optional=False, level=1, class_restriction=""):
		self.name = name
		self.configuration = {
			"items": uids,
			"optional": optional
		}
		self.level = level
		self.class_restriction = class_restriction

	def getData(self, importer):
		data = super().getData(importer)

		data["configuration"] = self.configuration
		data["level"] = self.level
		if self.name: data["title"] = self.name
		data["classRestriction"] = self.class_restriction

		return data


class ItemChoice(Advancement):
	def __init__(
		self,
		name=None,
		hint="",
		choices=[],
		allow_drops=True,
		item_type=None,
		pool=[],
		power_ability="",
		power_preparation="",
		power_uses_per="",
		power_uses_max="",
		restriction_type="",
		restriction_subtype="",
		restriction_level="",
		level=1,
		class_restriction=""
	):
		self.name = name
		self.configuration = {
			"hint": hint,
			"choices": choices,
			"allowDrops": allow_drops,
			"type": item_type,
			"pool": pool,
			"power": {
				"ability": power_ability,
				"preparation": power_preparation,
				"uses": {
					"per": power_uses_per,
					"max": power_uses_max,
				},
			},
			"restriction": {
				"type": restriction_type,
				"subtype": restriction_subtype,
				"level": restriction_level,
			},
		}
		self.level = level
		self.class_restriction = class_restriction

	def getData(self, importer):
		data = super().getData(importer)

		data["configuration"] = self.configuration
		data["level"] = self.level
		if self.name: data["title"] = self.name
		data["classRestriction"] = self.class_restriction

		return data


