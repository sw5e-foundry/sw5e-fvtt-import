import pickle, json, requests, os, re, sys
import sw5e.Class, sw5e.Archetype, sw5e.Species, sw5e.Background
import sw5e.ClassImprovement, sw5e.MulticlassImprovement, sw5e.SplashclassImprovement, sw5e.WeaponFocus, sw5e.WeaponSupremacy
import sw5e.Feature, sw5e.Feat, sw5e.FightingStyle, sw5e.FightingMastery, sw5e.LightsaberForm
import sw5e.Equipment, sw5e.Power, sw5e.EnhancedItem, sw5e.Maneuvers
import sw5e.ArmorProperty, sw5e.WeaponProperty, sw5e.Conditions
import sw5e.Monster
import utils.text

def withEntityTypes(cls):
	for entity_type in cls._Importer__stored_types:
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
		'maneuvers',
		'monster',
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
	__stored_types = __entity_types #+ [ 'monsterBehaviour' ]

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
				for entity_type in self.__stored_types:
					setattr(self, entity_type, old_data[entity_type])
		else:
			print('Unable to locate pickle file, loading from API')
			self.update(msg='Loading...')

		print('Applying foundry data...')
		if os.path.isfile(self.__foundry_data_path):
			missing_entity = 0
			with open(self.__foundry_data_path, 'r') as foundry_data_file:
				data = json.load(foundry_data_file)
				for uid in data: missing_entity = self.__applyFoundryData(uid, data[uid], missing=missing_entity)
			if missing_entity > self.warn_limit: print(f'	And {missing_entity-self.warn_limit} more...')

			missing_fdata = 0
			for entity_type in self.__stored_types:
				storage = self.getEntityList(entity_type)
				for uid in storage:
					entity = storage[uid]
					if not entity.foundry_id:
						## TODO: Remove this once starship items are done
						if re.search(r'EnhancedItem\.name-ship', uid): continue
						## TODO: Find a way to set the foundry_ids of the weapon modes
						if entity.__class__.__name__ == 'Weapon' and utils.text.getProperty('Auto', entity.propertiesMap): continue
						if entity.__class__.__name__ == 'Weapon' and entity.modes: continue
						if missing_fdata <= self.warn_limit: print(f'	Entity missing it\'s foundry data: {uid}')
						missing_fdata += 1
			if missing_fdata > self.warn_limit: print(f'	And {missing_fdata-self.warn_limit} more...')

			if missing_entity == 0 and missing_fdata == 0: print('	.')
		else:
			print('	Unable to open foundry data file')

	def __del__(self):
		# with open(self.__pickle_path, 'wb+') as pickle_file:
		# 	print('Saving...')
		# 	data = { entity_type: getattr(self, entity_type) for entity_type in self.__stored_types }
		# 	pickle.dump(data, pickle_file)
		pass

	def __applyFoundryData(self, uid, data, parent=None, missing=0):
		entity_type = uid.split('.')[0]
		if entity_type not in self.__stored_types: entity_type = utils.text.lowerCase(entity_type)
		base_uid = re.sub(r'\.mode-\w+$', '', uid)
		entity = (parent or self).get(entity_type, uid=base_uid)
		if entity:
			entity.foundry_id = data["id"]
			if "effects" in data: entity.effects = data["effects"]
			if "sub_entities" in data:
				for sub_uid in data["sub_entities"]:
					missing = self.__applyFoundryData(sub_uid, data["sub_entities"][sub_uid], entity, missing=missing)
		else:
			if missing <= self.warn_limit:
				print(f'	Foundry data for uid {uid}, but no such entity exists')
				if parent: print(f'	Parent: {parent.uid}')
			missing += 1
		return missing

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

	def getEntityList(self, entity_type):
		if entity_type in self.__stored_types:
			return getattr(self, entity_type)

	def __getClass(self, entity_type):
		entity_type = utils.text.capitalCase(entity_type)
		return getattr(getattr(sw5e, entity_type), entity_type)

	def get(self, entity_type, uid=None, data=None, loud=False):
		if entity_type in ('backpack', 'consumable', 'equipment', 'loot', 'tool', 'weapon'):
			entity_type = 'equipment'

		if (not uid) and data:
			klass = self.__getClass(entity_type)
			kklass = klass.getClass(data)
			uid = kklass.getUID(data)

		storage = self.getEntityList(entity_type) or {}

		if loud: print(f'Importer.get | {uid=}')

		return storage.get(uid, None)

	def __processEntity(self, raw_entity, entity_type, depth=0):
		if depth > 10:
			raise RecursionError(raw_entity["name"])
		try:
			storage = self.getEntityList(entity_type)
			klass = self.__getClass(entity_type)

			kklass = klass.getClass(raw_entity)
			uid = kklass.getUID(raw_entity)

			old_entity = self.get(entity_type, uid=uid)

			if (not old_entity) or (old_entity.timestamp != raw_entity["timestamp"]) or (old_entity.importer_version != self.version) or (old_entity.broken_links):
				new_entity = kklass(raw_entity, old_entity, uid, self)
				storage[uid] = new_entity
				sub_entities = new_entity.getSubEntities(self)
				for sub_entity, entity_type in sub_entities:
					self.__processEntity(sub_entity, entity_type, depth+1)
		except:
			print(f'		{raw_entity["name"]}')
			raise

	def update(self, msg='Updating...'):
		print(msg)

		for entity_type in self.__entity_types:
			if data := self.__getData(entity_type):
				print(f'	{entity_type}')
				for raw_entity in data:
					self.__processEntity(raw_entity, entity_type)

		extra_files = os.listdir(self.__extras_path)
		if extra_files:
			print("Extras...")
			for file_name in extra_files:
				if file_name.endswith('-old'): continue
				if data := self.__getExtraData(file_name):
					for entity_type in self.__stored_types:
						if entity_type in data:
							print(f'	{file_name} ({entity_type})')
							for raw_entity in data[entity_type]:
								self.__processEntity(raw_entity, entity_type)

	def output(self, msg='Output...'):
		print(msg)
		data = {}
		for entity_type in self.__stored_types:
			print(f'	{entity_type}')
			storage = self.getEntityList(entity_type)
			for uid in storage:
				entity = storage[uid]
				try:
					entity_data, file = entity.getData(self), entity.getFile(self)
					if file not in data:
						data[file] = {}
					for mode in entity_data:
						mode_uid = mode["flags"]["uid"]
						data[file][mode_uid] = mode
				except:
					print(f'		{entity.name}')
					raise

		print('Saving...')
		for file in data:
			print(f'	{file}')
			with open(f'{self.__output_path}{file}.json', 'w+', encoding='utf8') as output_file:
				if data[file]:
					json.dump(data[file], output_file, indent=4, sort_keys=False, ensure_ascii=False)
