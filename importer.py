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
	__stored_types = __entity_types

	__base_url = "https://sw5eapi.azurewebsites.net/api"
	version = 3

	warn_limit = 5

	def __init__(self, refresh=False):

		if refresh:
			for entity_type in self.__entity_types:
				data = self.__getData(entity_type, online=True)
				self.__saveData(entity_type, data)

		self.__loadRawData()
		self.__loadFoundryData()
		self.__processEntities()

	def __del__(self):
		# with open(self.__pickle_path, 'wb+') as pickle_file:
		# 	print('Saving...')
		# 	data = { entity_type: getattr(self, entity_type) for entity_type in self.__stored_types }
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


	def __loadRawData(self):
		print('Loading raw data...')
		for entity_type in self.__entity_types:
			if data := self.__getData(entity_type):
				print(f'	{entity_type}')
				for raw_entity in data:
					self.__loadEntity(raw_entity, entity_type)

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
								self.__loadEntity(raw_entity, entity_type)

	def __loadEntity(self, raw_entity, entity_type, depth=0):
		if depth > 10: raise RecursionError(raw_entity["name"])
		try:
			storage = self.getEntityList(entity_type)
			klass = self.__getClass(entity_type)

			kklass = klass.getClass(raw_entity)
			uid = kklass.getUID(raw_entity)

			if old_entity := storage.get(uid):
				if "propertiesMap" in raw_entity and "Modal" in raw_entity["propertiesMap"]: return
				elif raw_entity["partitionKey"] != old_entity.raw_partitionKey:
					if 'MISSING-DATA' in (raw_entity["partitionKey"], old_entity.raw_partitionKey):
						raise ValueError("Duplicated Entity in 'Missing Data'")
					elif old_entity.raw_partitionKey == 'Core':
						return
				else: raise ValueError("Duplicated Entity", uid)

			new_entity = kklass(raw_entity, uid=uid, importer=self)
			if new_entity.isValid():
				storage[uid] = new_entity

				sub_entities = new_entity.getSubEntities(importer=self)
				for sub_entity, entity_type in sub_entities:
					self.__loadEntity(sub_entity, entity_type, depth+1)
		except:
			print(f'		{raw_entity["name"]} {depth=}')
			print(f'		{uid}')
			raise

	def __loadFoundryData(self):
		print('Loading foundry data...')
		if os.path.isfile(self.__foundry_data_path):
			print('	Applying foundry data...')
			missing_entity = 0
			with open(self.__foundry_data_path, 'r') as foundry_data_file:
				data = json.load(foundry_data_file)
				for uid in data: missing_entity = self.__applyFoundryData(uid, data[uid], missing=missing_entity)
			if missing_entity > self.warn_limit: print(f'		And {missing_entity-self.warn_limit} more...')

			print('	Checking for missing foundry data...')
			missing_fdata = 0
			for entity_type in self.__stored_types:
				storage = self.getEntityList(entity_type)
				for uid, entity in storage.items():
					if not entity.foundry_id:
						## TODO: Remove this once starship items are done
						if re.search(r'EnhancedItem\.name-ship', uid): continue
						## TODO: Find a way to set the foundry_ids of the weapon modes
						if entity.__class__.__name__ == 'Weapon' and utils.text.getProperty('Auto', entity.raw_propertiesMap): continue
						if entity.__class__.__name__ == 'Weapon' and entity.raw_modes: continue
						if missing_fdata < self.warn_limit: print(f'		Entity missing it\'s foundry data: {uid}')
						entity.foundry_id = utils.text.randomID()
						missing_fdata += 1
			if missing_fdata > self.warn_limit: print(f'		And {missing_fdata-self.warn_limit} more...')

			# if missing_entity == 0 and missing_fdata == 0: print('	.')
		else:
			print('	Unable to open foundry data file')

	def __applyFoundryData(self, uid, data, parent=None, missing=0):
		entity_type = uid.split('.')[0]
		if entity_type not in self.__stored_types: entity_type = utils.text.lowerCase(entity_type)

		base_uid = re.sub(r'\.mode-\w+$', '', uid)
		entity = (parent or self).get(entity_type, uid=base_uid, fid_required=False)

		if entity:
			entity.foundry_id = data["id"]
			if "effects" in data: entity.effects = data["effects"]
			if "sub_entities" in data:
				for sub_uid, sub_data in data["sub_entities"].items():
					missing = self.__applyFoundryData(sub_uid, sub_data, parent=entity, missing=missing)
		else:
			if missing < self.warn_limit:
				print(f'		Foundry data for uid {uid}, but no such entity exists')
				if parent: print(f'		Parent: {parent.uid}')
			missing += 1
		return missing

	def __processEntities(self, depth=0):
		print(f'Processing Entities... {depth}')
		broken_links = []
		for entity_type in self.__stored_types:
			printed = False
			storage = self.getEntityList(entity_type)
			for uid, entity in storage.items():
				if not printed:
					print(f'	{entity_type}')
					printed = True
				if len(entity.broken_links) or not entity.processed:
					try:
						entity.process(importer=self)
					except:
						print(f'		{uid=} {depth=}')
						raise
				if entity.broken_links: broken_links.append([entity.name, entity.broken_links])
		if depth >= 5:
			any_non_id_error = False
			for entity, errors in broken_links:
				for error in errors:
					if error != 'no foundry id':
						any_non_id_error = True
			if any_non_id_error: raise RecursionError(broken_links)
			else: print(broken_links)
		if len(broken_links): self.__processEntities(depth=depth+1)


	def getEntityList(self, entity_type):
		if entity_type in self.__stored_types:
			return getattr(self, entity_type)

	def __getClass(self, entity_type):
		entity_type = utils.text.capitalCase(entity_type)
		return getattr(getattr(sw5e, entity_type), entity_type)

	def getUID(self, entity_type, raw_entity):
		klass = self.__getClass(entity_type)
		kklass = klass.getClass(raw_entity)
		return kklass.getUID(raw_entity)


	def get(self, entity_type, uid=None, data=None, loud=False, fid_required=True):
		if entity_type in ('backpack', 'consumable', 'equipment', 'loot', 'tool', 'weapon'):
			entity_type = 'equipment'

		if (not uid) and data: uid = self.getUID(entity_type, data)

		storage = self.getEntityList(entity_type) or {}

		if loud: print(f'Importer.get | {uid=}')

		entity = storage.get(uid, None)
		if fid_required and entity and not entity.foundry_id: raise AssertionError('Entities should have foundry_id by now')

		return entity


	def output(self, msg='Output...'):
		print(msg)
		data = {}
		for entity_type in self.__stored_types:
			print(f'	{entity_type}')
			storage = self.getEntityList(entity_type)
			for uid in storage:
				entity = storage[uid]
				try:
					entity_data, file = entity.getData(importer=self), entity.getFile(importer=self)
					if file not in data:
						data[file] = {}
					for mode in entity_data:
						mode_uid = mode["flags"]["sw5e-importer"]["uid"]
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
