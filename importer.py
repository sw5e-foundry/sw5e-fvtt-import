import pickle, json, requests, os.path, re
import sw5e.Class, sw5e.Archetype, sw5e.Feature, sw5e.Species, sw5e.Feat, sw5e.Equipment, sw5e.Power
import sw5e.ArmorProperty, sw5e.WeaponProperty, sw5e.Conditions
import utils.text

def withItemTypes(cls):
	for item_type in cls._Importer__item_types:
		setattr(cls, item_type, {})
	return cls

@withItemTypes
class Importer:
	__pickle_path = "importer.pickle"
	__output_path = "output/"
	__foundry_ids_path = "foundry_ids.json"
	__foundry_effects_path = "foundry_effects.json"
	__raw_path = "raw/"
	__item_types = [
		'archetype',
		'armorProperty',
		# 'background',
		'class',
		'conditions',
		# # 'deployment',
		# 'enhancedItem',
		'equipment',
		'feat',
		'feature',
		# 'fightingMastery',
		# 'fightingStyle',
		# 'lightsaberForm',
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
	# __item_types = [ 'equipment' ]
	__base_url = "https://sw5eapi.azurewebsites.net/api"
	version = 1

	def __init__(self):
		if os.path.isfile(self.__pickle_path):
			print('Loading...')
			with open(self.__pickle_path, 'rb') as pickle_file:
				old_data = pickle.load(pickle_file)
				for item_type in self.__item_types:
					setattr(self, item_type, old_data[item_type])
		else:
			print('Unable to locate pickle file, loading from API')
			self.update(msg='Loading...')

		print('Loading foundry ids...')
		if os.path.isfile(self.__foundry_ids_path):
			missing = 0
			with open(self.__foundry_ids_path, 'r') as ids_file:
				data = json.load(ids_file)
				for uid in data:
					item_type = uid.split('.')[0]
					item_type = item_type[:1].lower() + item_type[1:]
					item = self.get(item_type, uid=uid)
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
			for item_type in self.__item_types:
				storage = self.__getItemList(item_type)
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
					item_type = uid.split('.')[0].lower()
					item = self.get(item_type, uid=uid)
					if item:
						item.effects = data[uid]
					else:
						## Don't print an error for alternate weapon modes, as those are only generated on the output method
						if re.search(r'((?:\w+-\w+\.)+)mode-(\w+)', uid):
							continue
						elif missing < 10:
							print(f'	Active effect for uid {uid}, but no such item exists')
							missing += 1
			missing = 0
			for item_type in self.__item_types:
				storage = self.__getItemList(item_type)
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
		# 	data = { item_type: getattr(self, item_type) for item_type in self.__item_types }
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

	def __getItemList(self, item_type):
		if item_type in self.__item_types:
			return getattr(self, item_type)

	def __getClass(self, item_type):
		item_type = item_type[:1].upper() + item_type[1:]
		return getattr(getattr(sw5e, item_type), item_type)

	def get(self, item_type, uid=None, data=None):
		if item_type in ('backpack', 'consumable', 'equipment', 'loot', 'tool', 'weapon'):
			item_type = 'equipment'

		if (not uid) and data:
			klass = self.__getClass(item_type)
			kklass = klass.getClass(data)
			uid = kklass.getUID(data)
			# print(f'{uid=}')

		storage = self.__getItemList(item_type) or {}
		if uid in storage:
			return storage[uid]
		else:
			return None

	def update(self, msg='Updating...', online=False):
		msg += ' (Online)' if online else ' (Offline)'
		print(msg)
		for item_type in self.__item_types:
			print(f'	{item_type}')
			data = self.__getData(item_type, online)
			if online: self.__saveData(item_type, data)

			storage = self.__getItemList(item_type)
			klass = self.__getClass(item_type)

			for raw_item in data:
				try:
					kklass = klass.getClass(raw_item)
					uid = kklass.getUID(raw_item)
					old_item = self.get(item_type, uid=uid)
					if (not old_item) or (old_item.timestamp != raw_item["timestamp"]) or (old_item.importer_version != self.version) or (old_item.broken_links):
						new_item = kklass(raw_item, old_item, uid, self)
						storage[uid] = new_item
				except:
					print(f'		{raw_item["name"]}')
					raise

	def output(self, msg='Output...'):
		print(msg)
		data = {}
		for item_type in self.__item_types:
			print(f'	{item_type}')
			storage = self.__getItemList(item_type)
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
