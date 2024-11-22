from sw5e.templates import Template
import sw5e.Activity, utils.object, copy

class Activities(Template):
	def dataMap(self):
		return {
			**super().dataMap(),
			'system.activities': 'activities',
		}

	def activitiesHelper(self, data):
		activities = []
		if action_type := data.get('action_type'):
			if action_type == 'save':
				activities.append(sw5e.Activity.Save(data))
			elif action_type in ['msak', 'mwak', 'rsak', 'rwak']:
				utils.object.setProperty(data, 'attack.type', 'melee' if action_type.startswith('m') else 'ranged', force=True)
				utils.object.setProperty(data, 'attack.classification', 'spell' if action_type[1] == 's' else 'weapon', force=True)
				attackActivity = sw5e.Activity.Attack(data)
				activities.append(attackActivity)
				if properties := data.get('properties'):
					if (properties.get("burst")):
						burst_data = copy.deepcopy(data)
						utils.object.setProperty(burst_data, 'name', 'Burst Attack')
						utils.object.setProperty(burst_data, 'target.value', 10)
						utils.object.setProperty(burst_data, 'target.units', 'ft')
						utils.object.setProperty(burst_data, 'target.type', 'cube')
						utils.object.setProperty(burst_data, 'save.ability', 'dex')
						if utils.object.getProperty(burst_data, 'save.dc') == None:
							utils.object.setProperty(burst_data, 'save.scaling', 'dex')
						# TODO: set 'consume' to the ammount of ammo burst uses
						# burst_data = self.getAutoTargetData(burst_data, burst_or_rapid=True)
						activities.append(sw5e.Activity.Save(burst_data))
					if (properties.get("rapid")):
						rapid_data = copy.deepcopy(data)
						utils.object.setProperty(rapid_data, 'name', 'Rapid Attack')
						utils.object.setProperty(rapid_data, 'save.ability', 'dex')
						if utils.object.getProperty(rapid_data, 'save.dc') == None:
							utils.object.setProperty(rapid_data, 'save.scaling', 'dex')
						if len(rapid_data["damage"].parts) >= 1:
							dmg = rapid_data["damage"].parts[0]
							dmg.number = dmg.number * 2
						# TODO: set 'consume' to the ammount of ammo rapid uses
						# rapid_data = self.getAutoTargetData(burst_data, burst_or_rapid=True)
						activities.append(sw5e.Activity.Save(rapid_data))
					if (properties.get("auto")):
						activities.remove(attackActivity)
			elif action_type == 'other':
				if "damage" in data and len(data["damage"].parts):
					activities.append(sw5e.Activity.Damage(data))
				elif utils.object.getProperty(data, 'activation.type'):
					activities.append(sw5e.Activity.Utility(data))
			elif action_type == 'abil':
				activities.append(sw5e.Activity.Check(data))
		if healing := data.get('healing'):
			activities.append(sw5e.Activity.Heal(data))
		return activities

	def getActivitiesData(self):
		raise NotImplementedError()
	def getActivities(self):
		data = self.getActivitiesData()
		activities = self.activitiesHelper(data)
		return activities

	def processActivitiesData(self, importer):
		raise NotImplementedError()
	def processActivities(self, importer):
		if self.activities == None: return
		data = self.processActivitiesData(importer)
		activities = self.activitiesHelper(data)
		self.activities.extend(activities)

	def getDataActivities(self, importer):
		return { activity.id: activity.getData(importer) for activity in self.activities } if self.activities else None
