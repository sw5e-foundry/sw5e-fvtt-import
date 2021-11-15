import pickle, json, requests, os, re, sys
import sw5e.Class, sw5e.Archetype, sw5e.Species, sw5e.Background
import sw5e.ClassImprovement, sw5e.MulticlassImprovement, sw5e.SplashclassImprovement, sw5e.WeaponFocus, sw5e.WeaponSupremacy
import sw5e.Feature, sw5e.Feat, sw5e.FightingStyle, sw5e.FightingMastery, sw5e.LightsaberForm
import sw5e.Equipment, sw5e.Power, sw5e.EnhancedItem
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
	__foundry_data_path = "foundry_data.json"
	__raw_path = "raw/"
	__extras_path = "extras/"
	__entity_types = [
		'archetype',
		'armorProperty',
		'background',
		'class',
		'conditions',
		'enhancedItem',
		'equipment',
		'feat',
		'feature',
		'fightingMastery',
		'fightingStyle',
		'lightsaberForm',
		# 'monster',
		'power',
		# 'referenceTable',
		# 'skills',
		'species',
		# # 'starshipDeployment',
		# # 'starshipEquipment',
		# # 'starshipModification',
		# # 'starshipBaseSize',
		# # 'starshipVenture',
		'weaponProperty',
		'ClassImprovement',
		'MulticlassImprovement',
		'SplashclassImprovement',
		'WeaponFocus',
		'WeaponSupremacy',
	]

	# __entity_types = [ 'background' ]
	__base_url = "https://sw5eapi.azurewebsites.net/api"
	version = 1

	warn_limit = 15

	def __init__(self, mode=''):

		if mode == 'refresh':
			for entity_type in self.__entity_types:
				data = self.__getData(entity_type, online=True)
				self.__saveData(entity_type, data)

		if os.path.isfile(self.__pickle_path):
			print('Loading...')
			with open(self.__pickle_path, 'rb') as pickle_file:
				old_data = pickle.load(pickle_file)
				for entity_type in self.__entity_types:
					setattr(self, entity_type, old_data[entity_type])
		else:
			print('Unable to locate pickle file, loading from API')
			self.update(msg='Loading...')

		print('Loading foundry data...')
		if os.path.isfile(self.__foundry_data_path):
			missing = 0
			with open(self.__foundry_data_path, 'r') as foundry_data_file:
				data = json.load(foundry_data_file)
				for uid in data:
					entity_type = uid.split('.')[0]
					if entity_type not in self.__entity_types:
						entity_type = utils.text.lowerCase(entity_type)
					new_uid = re.sub(r'\.mode-\w+$', '', uid)
					item = self.get(entity_type, uid=new_uid)
					if item:
						item.foundry_id = data[uid]["id"]
						if "effects" in data[uid]: item.effects = data[uid]["effects"]
					else:
						if missing <= self.warn_limit:
							print(f'	Foundry data for uid {uid}, but no such item exists')
						missing += 1
			if missing > self.warn_limit: print(f'	And {missing-self.warn_limit} more...')

			missing = 0
			for entity_type in self.__entity_types:
				storage = self.__getItemList(entity_type)
				for uid in storage:
					item = storage[uid]
					if not item.foundry_id:
						## TODO: Remove this once starship items are done
						if re.search(r'EnhancedItem\.name-ship', uid): continue
						## TODO: Find a way to set the foundry_ids of the weapon modes
						if item.__class__.__name__ == 'Weapon' and utils.text.getProperty('Auto', item.propertiesMap): continue
						if item.__class__.__name__ == 'Weapon' and item.modes: continue
						if missing <= self.warn_limit:
							print(f'	Item missing it\'s foundry data: {uid}')
						missing += 1
			if missing > self.warn_limit: print(f'	And {missing-self.warn_limit} more...')
		else:
			print('	Unable to open foundry data file')

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
			path = f'{self.__raw_path}{file_name}.json'
			if not os.path.isfile(path): 
				data = self.__getData(file_name, online=True)
				self.__saveData(file_name, data)
				return data
			with open(path, 'r+', encoding='utf8') as raw_file:
				data = json.load(raw_file)
		return data

	def __getExtraData(self, file_name):
		data = None
		path = f'{self.__extras_path}{file_name}'
		if os.path.isfile(path): 
			with open(path, 'r+', encoding='utf8') as raw_file:
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

	def get(self, entity_type, uid=None, data=None, loud=False):
		if entity_type in ('backpack', 'consumable', 'equipment', 'loot', 'tool', 'weapon'):
			entity_type = 'equipment'

		if (not uid) and data:
			klass = self.__getClass(entity_type)
			kklass = klass.getClass(data)
			uid = kklass.getUID(data)

		storage = self.__getItemList(entity_type) or {}

		if loud: print(f'Importer.get | {uid=}')

		if uid in storage:
			return storage[uid]
		else:
			return None

	def __processItem(self, raw_item, entity_type, depth=0):
		if depth > 10:
			raise RecursionError(raw_item["name"])
		try:
			storage = self.__getItemList(entity_type)
			klass = self.__getClass(entity_type)

			kklass = klass.getClass(raw_item)
			uid = kklass.getUID(raw_item)

			old_item = self.get(entity_type, uid=uid)

			if (not old_item) or (old_item.timestamp != raw_item["timestamp"]) or (old_item.importer_version != self.version) or (old_item.broken_links):
				new_item = kklass(raw_item, old_item, uid, self)
				storage[uid] = new_item
				sub_items = new_item.getSubItems(self)
				for sub_item, entity_type in sub_items:
					self.__processItem(sub_item, entity_type, depth+1)
		except:
			print(f'		{raw_item["name"]}')
			raise

	def update(self, msg='Updating...'):
		print(msg)

		for entity_type in self.__entity_types:
			if data := self.__getData(entity_type):
				print(f'	{entity_type}')
				for raw_item in data:
					self.__processItem(raw_item, entity_type)

		extra_files = os.listdir(self.__extras_path)
		if extra_files:
			print("Extras...")
			for file_name in extra_files:
				if data := self.__getExtraData(file_name):
					for entity_type in self.__entity_types:
						if entity_type in data:
							print(f'	{file_name} ({entity_type})')
							for raw_item in data[entity_type]:
								self.__processItem(raw_item, entity_type)

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
						mode_uid = mode["flags"]["uid"]
						data[file][mode_uid] = mode
				except:
					print(f'		{item.name}')
					raise

		for file in data:
			with open(f'{self.__output_path}{file}.json', 'w+', encoding='utf8') as output_file:
				if data[file]:
					json.dump(data[file], output_file, indent=4, sort_keys=False, ensure_ascii=False)
