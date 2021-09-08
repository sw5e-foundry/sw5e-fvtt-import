import pickle, json, requests, os.path
import sw5e.Class, sw5e.Archetype, sw5e.Feature, sw5e.Species, sw5e.Feat, sw5e.Equipment

def withItemTypes(cls):
	for item_type in cls._Importer__item_types:
		setattr(cls, item_type, {})
	return cls

@withItemTypes
class Importer:
	__pickle_path = "importer.pickle"
	__output_path = "output/"
	__foundry_ids_path = "foundry_ids.json"
	__raw_path = "raw/"
	__item_types = [
		'archetype',
		# # 'armorProperty',
		# 'background',
		'class',
		# # 'conditions',
		# # 'deployment',
		# 'enhancedItem',
		'equipment',
		'feat',
		'feature',
		# 'fightingMastery',
		# 'fightingStyle',
		# 'lightsaberForm',
		# 'monster',
		# 'power',
		# 'referenceTable',
		# # 'skills',
		'species',
		# # 'starshipEquipment',
		# # 'starshipModification',
		# # 'starshipSizes',
		# # 'venture',
		# # 'weaponProperty',
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
			self.update(msg='Loading...')

		if os.path.isfile(self.__foundry_ids_path):
			print('Loading foundry ids...')
			with open(self.__foundry_ids_path, 'r') as ids_file:
				data = json.load(ids_file)
				for uid in data:
					item_type = uid.split('.')[0].lower()
					item = self.get(item_type, uid=uid)
					if item: item.foundry_id = data[uid]

	def __del__(self):
		# TODO: uncomment this when done editing the importer
		# with open(self.__pickle_path, 'wb+') as pickle_file:
		# 	print('Saving...')
		# 	data = { item_type: getattr(self, item_type) for item_type in self.__item_types }
		# 	pickle.dump(data, pickle_file)
		pass

	def __getData(self, file_name):
		r = requests.get(self.__base_url + '/' + file_name)
		data = json.loads(r.text)
		return data

	def __saveData(self, file_name, data):
		with open(f'{self.__raw_path}{file_name}.json', 'w+', encoding='utf8') as raw_file:
			json.dump(data, raw_file, indent=4, sort_keys=False, ensure_ascii=False)

	def __getItemList(self, item_type):
		if item_type in self.__item_types:
			return getattr(self, item_type)

	def __getClass(self, item_type):
		return getattr(getattr(sw5e, item_type.capitalize()), item_type.capitalize())

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

	def update(self, msg='Updating...'):
		print(msg)
		for item_type in self.__item_types:
			print(f'	{item_type}')

			data = self.__getData(item_type)
			self.__saveData(item_type, data)

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
		for item_type in self.__item_types:
			print(f'	{item_type}')
			storage = self.__getItemList(item_type)
			with open(f'{self.__output_path}{item_type}.json', 'w+', encoding='utf8') as output_file:
				# data = []
				# for uid in storage:
				# 	item = storage[uid]
				# 	try:
				# 		data += item.getData(self)
				# 	except:
				# 		print(f'		{item.name}')
				# 		raise
				# if data:
				# 	json.dump(data, output_file, indent=4, sort_keys=False, ensure_ascii=False)

				data = {}
				for uid in storage:
					item = storage[uid]
					try:
						data[uid] = item.getData(self)
					except:
						print(f'		{item.name}')
						raise
				if data:
					json.dump(data, output_file, indent=4, sort_keys=False, ensure_ascii=False)
