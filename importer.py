import pickle, json, requests, os.path
import sw5e.Class, sw5e.Archetype, sw5e.Feature, sw5e.Species, sw5e.Feat, sw5e.Equipment

def withItemTypes(cls):
	for item_type in cls._Importer__item_types:
		setattr(cls, item_type, [])
	return cls

@withItemTypes
class Importer:
	__pickle_path = "importer.pickle"
	__output_path = "output/"
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

	def get(self, item_type, *args, **kwargs):
		items = self.__getItemList(item_type) or []
		for item in items:
			if item.matches(*args, **kwargs):
				return item

	def update(self, msg='Updating...'):
		print(msg)
		for item_type in self.__item_types:
			print(f'	{item_type}')

			data = self.__getData(item_type)
			self.__saveData(item_type, data)

			storage = self.__getItemList(item_type)
			klass = getattr(getattr(sw5e, item_type.capitalize()), item_type.capitalize())

			for raw_item in data:
				try:
					old_item = self.get(item_type, raw_item)
					if (not old_item) or (old_item.timestamp != raw_item["timestamp"]) or (old_item.importer_version != self.version) or (old_item.brokenLinks):
						kklass = klass.getClass(raw_item)
						new_item = kklass(raw_item, old_item, self)
						if old_item: storage.remove(old_item)
						storage.append(new_item)
				except:
					print(f'		{raw_item["name"]}')
					raise

	def output(self, msg='Output...'):
		print(msg)
		for item_type in self.__item_types:
			print(f'	{item_type}')
			items = self.__getItemList(item_type)
			with open(f'{self.__output_path}{item_type}.json', 'w+', encoding='utf8') as output_file:
				data = []
				for item in items:
					try:
						data += item.getData(self)
					except:
						print(f'		{item.name}')
						raise
				json.dump(data, output_file, indent=4, sort_keys=False, ensure_ascii=False)
