import pickle, json, requests, os.path, re
import sw5e.Class, sw5e.Archetype, sw5e.Species, sw5e.Background
import sw5e.Feature, sw5e.Feat, sw5e.FightingStyle, sw5e.FightingMastery, sw5e.LightsaberForm
import sw5e.Equipment, sw5e.Power
import sw5e.ArmorProperty, sw5e.WeaponProperty, sw5e.Conditions
import utils.text

def withEntityTypes(cls):
	for entity_type in cls._Importer__entity_types:
		setattr(cls, entity_type, {})
	return cls

@withEntityTypes
class Importer:
	__pickle_path = "importer.pickle"
	__output_path = "output/"
	__foundry_ids_path = "foundry_ids.json"
	__foundry_effects_path = "foundry_effects.json"
	__raw_path = "raw/"
	__entity_types = [
		'archetype',
		'armorProperty',
		'background',
		'class',
		'conditions',
		# # 'deployment',
		# 'enhancedItem',
		'equipment',
		'feat',
		'feature',
		'fightingMastery',
		'fightingStyle',
		'lightsaberForm',
		# 'monster',
		'power',
		# 'referenceTable',
		'species',
		# # 'starshipEquipment',
		# # 'starshipModification',
		# # 'starshipSizes',
		# # 'venture',
		'weaponProperty',
	]
	# __entity_types = [ 'background' ]
	__base_url = "https://sw5eapi.azurewebsites.net/api"
	version = 1

	def __init__(self):
		if os.path.isfile(self.__pickle_path):
			print('Loading...')
			with open(self.__pickle_path, 'rb') as pickle_file:
				old_data = pickle.load(pickle_file)
				for entity_type in self.__entity_types:
					setattr(self, entity_type, old_data[entity_type])
		else:
			print('Unable to locate pickle file, loading from API')
			self.update(msg='Loading...')

		print('Loading foundry ids...')
		if os.path.isfile(self.__foundry_ids_path):
			missing = 0
			with open(self.__foundry_ids_path, 'r') as ids_file:
				data = json.load(ids_file)
				for uid in data:
					entity_type = uid.split('.')[0]
					entity_type = utils.text.lowerCase(entity_type)
					item = self.get(entity_type, uid=uid)
					if item:
						item.foundry_id = data[uid]
					else:
						## Don't print an error for alternate weapon modes, as those are only generated on the output method
						if re.search(r'((?:\w+-\w+\.)+)mode-(\w+)', uid):
							continue
						elif missing < 10:
							print(f'	Foundry id for uid {uid}, but no such item exists')
							missing += 1
			missing = 0
			for entity_type in self.__entity_types:
				storage = self.__getItemList(entity_type)
				for uid in storage:
					item = storage[uid]
					if not item.foundry_id:
						## TODO: Find a way to set the foundry_ids of the weapon modes
						if item.__class__.__name__ == 'Weapon' and utils.text.getProperty('Auto', item.propertiesMap): continue
						if item.__class__.__name__ == 'Weapon' and item.modes: continue
						if missing < 10:
							print(f'	Item missing it\'s foundry_id: {uid}')
							missing += 1
		else:
			print('	Unable to open foundry ids file')

		print('Loading active effects...')
		if os.path.isfile(self.__foundry_effects_path):
			missing = 0
			with open(self.__foundry_effects_path, 'r') as effects_file:
				data = json.load(effects_file)
				for uid in data:
					entity_type = uid.split('.')[0]
					entity_type = utils.text.lowerCase(entity_type)
					item = self.get(entity_type, uid=uid)
					if item:
						item.effects = data[uid]
					else:
						## Don't print an error for alternate weapon modes, as those are only generated on the output method
						if re.search(r'((?:\w+-\w+\.)+)mode-(\w+)', uid):
							continue
						elif missing < 10:
							print(f'	Active effects for uid {uid}, but no such item exists')
							missing += 1
			missing = 0
			for entity_type in self.__entity_types:
				storage = self.__getItemList(entity_type)
				for uid in storage:
					item = storage[uid]
					if hasattr(item, 'effects') and item.effects == None:
						## TODO: Find a way to set the active effects of the weapon modes
						if item.__class__.__name__ == 'Weapon' and utils.text.getProperty('Auto', item.propertiesMap): continue
						if item.__class__.__name__ == 'Weapon' and item.modes: continue
						if missing < 10:
							print(f'	Item missing it\'s active effects: {uid}')
							missing += 1
		else:
			print('	Unable to open active effects file')

	def __del__(self):
		# with open(self.__pickle_path, 'wb+') as pickle_file:
		# 	print('Saving...')
		# 	data = { entity_type: getattr(self, entity_type) for entity_type in self.__entity_types }
		# 	pickle.dump(data, pickle_file)
		pass

	def __getData(self, file_name, online=False):
		data = None
		if online:
			r = requests.get(self.__base_url + '/' + file_name)
			data = json.loads(r.text)
		else:
			with open(f'{self.__raw_path}{file_name}.json', 'r+', encoding='utf8') as raw_file:
				data = json.load(raw_file)
		return data

	def __saveData(self, file_name, data):
		with open(f'{self.__raw_path}{file_name}.json', 'w+', encoding='utf8') as raw_file:
			json.dump(data, raw_file, indent=4, sort_keys=False, ensure_ascii=False)

	def __getItemList(self, entity_type):
		if entity_type in self.__entity_types:
			return getattr(self, entity_type)

	def __getClass(self, entity_type):
		entity_type = entity_type[:1].upper() + entity_type[1:]
		return getattr(getattr(sw5e, entity_type), entity_type)

	def get(self, entity_type, uid=None, data=None):
		if entity_type in ('backpack', 'consumable', 'equipment', 'loot', 'tool', 'weapon'):
			entity_type = 'equipment'

		if (not uid) and data:
			klass = self.__getClass(entity_type)
			kklass = klass.getClass(data)
			uid = kklass.getUID(data)
			# print(f'{uid=}')

		storage = self.__getItemList(entity_type) or {}
		if uid in storage:
			return storage[uid]
		else:
			return None

	def update(self, msg='Updating...', online=False):
		msg += ' (Online)' if online else ' (Offline)'
		print(msg)
		for entity_type in self.__entity_types:
			print(f'	{entity_type}')
			data = self.__getData(entity_type, online)
			if online: self.__saveData(entity_type, data)

			storage = self.__getItemList(entity_type)
			klass = self.__getClass(entity_type)

			for raw_item in data:
				try:
					kklass = klass.getClass(raw_item)
					uid = kklass.getUID(raw_item)
					old_item = self.get(entity_type, uid=uid)
					if (not old_item) or (old_item.timestamp != raw_item["timestamp"]) or (old_item.importer_version != self.version) or (old_item.broken_links):
						new_item = kklass(raw_item, old_item, uid, self)
						storage[uid] = new_item
				except:
					print(f'		{raw_item["name"]}')
					raise

	def output(self, msg='Output...'):
		print(msg)
		data = {}
		for entity_type in self.__entity_types:
			print(f'	{entity_type}')
			storage = self.__getItemList(entity_type)
			for uid in storage:
				item = storage[uid]
				try:
					item_data, file = item.getData(self), item.getFile(self)
					if file not in data:
						data[file] = {}
					for mode in item_data:
						data[file][mode["flags"]["uid"]] = mode
				except:
					print(f'		{item.name}')
					raise

		for file in data:
			with open(f'{self.__output_path}{file}.json', 'w+', encoding='utf8') as output_file:
				if data[file]:
					json.dump(data[file], output_file, indent=4, sort_keys=False, ensure_ascii=False)
