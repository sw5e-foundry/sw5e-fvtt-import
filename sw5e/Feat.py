import sw5e.Feature, utils.text
import re, json

class Feat(sw5e.Feature.BaseFeature):
	def load(self, raw_item):
		super().load(raw_item)

		self.attributesIncreased = utils.text.cleanJson(raw_item, "attributesIncreased")

	def process(self, old_item, importer):
		super().process(old_item, importer)

		if self.name in ('Class Improvement', 'Multiclass Improvement', 'Splashclass Improvement', 'Weapon Focused', 'Weapon Supremacist'):
			extra_text = ''
			name = self.name
			if name == 'Weapon Focused': name = 'WeaponFocus'
			elif name == 'Weapon Supremacist': name = 'WeaponSupremacy'
			else: name = re.sub(' ', '', self.name)
			storage = getattr(importer, name)
			for uid in storage:
				text = storage[uid].name
				if storage[uid].foundry_id:
					text = f'@Compendium[sw5e.feats.{storage[uid].foundry_id}]{{{text}}}'
				else:
					self.broken_links = True
				extra_text += f'\n- {text}'

			if extra_text:
				self.description["value"] += f'\n{utils.text.markdownToHtml(extra_text)}'
			else:
				self.broken_links = True

	def getImg(self):
		name = self.name
		name = re.sub(r'[ /]', r'%20', name)
		return f'systems/sw5e/packs/Icons/Feats/{name}.webp'
