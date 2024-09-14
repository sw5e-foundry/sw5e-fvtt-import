import sw5e.Entity, sw5e.Activity, utils.object

class Activities(sw5e.Entity.Entity):
	def processTemplates(self, importer):
		super().processTemplates(importer)
		self.activities = self.getActivities()

	def getActivitiesData(self):
		raise NotImplementedError()

	def getActivities(self):
		activities = []
		data = self.getActivitiesData()
		if action_type := data.get('action_type'):
			if action_type == 'save':
				activities.append(sw5e.Activity.Save(data))
			elif action_type in ['msak', 'mwak', 'rsak', 'rwak']:
				if action_type.startswith('r'): utils.object.setProperty(data, 'attack.type', 'ranged', force=True)
				if action_type[1] == 'w': utils.object.setProperty(data, 'attack.classification', 'weapon', force=True)
				activities.append(sw5e.Activity.Attack(data))
				if (versatile := data.get('versatile')) and (damage_type := utils.object.getProperty(data, 'damage.parts.0.1', default=None)):
					utils.object.setProperty(data, 'damage.parts', [[versatile, damage_type]])
					utils.object.setProperty(data, 'name', 'Versatile Damage')
					activities.append(sw5e.Activity.Attack(data))
			elif action_type == 'heal':
				activities.append(sw5e.Activity.Heal(data))
			elif action_type == 'other':
				if len(utils.object.getProperty(data, 'damage.parts')):
					activities.append(sw5e.Activity.Damage(data))
				elif utils.object.getProperty(data, 'activation.type'):
					activities.append(sw5e.Activity.Utility(data))
			elif action_type == 'abil':
				activities.append(sw5e.Activity.Check(data))
		return activities;

	def getData(self, importer):
		data = super().getData(importer)[0]

		if self.activities:
			utils.object.setProperty(data, 'system.activities', { activity.id: activity.getData(importer) for activity in self.activities }, force=True)

		return [data]
