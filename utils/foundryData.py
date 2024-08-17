import json, re

def cleanFoundryData(path='foundry_data.json'):
	data = loadJson(path)
	cleanEffects(data)
	saveJson(data, path)

def loadJson(path):
	with open(path, 'r+', encoding='utf8') as raw_file:
		return json.load(raw_file)

def saveJson(data, path):
	with open(path, 'w+', encoding='utf8') as raw_file:
		json.dump(data, raw_file, indent=4, sort_keys=False, ensure_ascii=False)

def cleanEffects(data):
	key_blacklist = [
		'system.details.background',
		'system.details.species',
		'system.traits.languages.value',
		'system.traits.toolProf.value',
	]
	key_blacklist_re = [
		r'system\.tools\.\w+\.prof',
	]
	def blacklisted(key):
		if key in key_blacklist: return True
		for k in key_blacklist_re:
			if re.match(k, key): return True
		return False
	key_whitelist = [
		'system.attributes.hp.bonuses.level',
		'system.attributes.hp.bonuses.overall',
		'system.traits.dr.value',
		'system.traits.di.value',
		'system.traits.dv.value',
		'system.traits.ci.value',
		'system.attributes.ac.value',
	]
	key_whitelist_re = [
		r'flags\.sw5e\..*',
	]
	def whitelisted(key):
		if key in key_whitelist: return True
		for k in key_whitelist_re:
			if re.match(k, key): return True
		return False

	for key, item in data.items():
		if "effects" not in item: continue
		itemType = key.split('.')[0]
		hasAdvancements = itemType in ["Archetype", "Class", "Species", "Background"]
		if hasAdvancements:
			for effect in item["effects"]:
				effect["changes"] = list([
					change for change in effect["changes"]
					if not blacklisted(change["key"])
				])
		item["effects"] = list([
			effect for effect in item["effects"]
			if len(effect["changes"])
		])
		if hasAdvancements and len(item["effects"]):
			non_whitelisted = [
				change
				for change in effect["changes"] if not whitelisted(change["key"])
				for effect in item["effects"]
			]
			if len(non_whitelisted):
				print(f'Item {key} still has non whitelisted effects:')
				print(non_whitelisted)
