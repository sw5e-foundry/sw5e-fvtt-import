import sw5e.Equipment, sw5e.templates, utils.text, utils.object
import re, json

class Backpack(
	sw5e.Equipment.Equipment,
	sw5e.templates.Currency,
):
	def load(self, raw_item):
		super().load(raw_item)

	def process(self, importer):
		super().process(importer)

		self.duration_value, self.duration_unit = None, 'inst'
		self.target_value, self.target_width, self.target_unit, self.target_type = None, None, None, None
		self.range_short, self.range_long, self.range_unit = None, None, None
		self.uses, self.recharge = None, None
		self.action_type, self.damage, self.formula, self.save, self.save_dc = None, None, None, None, None
		self.activation = None

	def getImg(self, importer=None):
		kwargs = {
			# 'item_type': self.equipmentCategory,
			# 'no_img': ('Unknown',),
			'default_img': 'modules/sw5e/icons/packs/Storage/Crate.webp',
			# 'plural': False
		}
		return super().getImg(importer=importer, **kwargs)

	def getType(self):
		return 'container'

	def getData(self, importer):
		data = super().getData(importer)[0]

		# TODO: Read capacity from the item's description
		# utils.object.setProperty(data, 'system.capacity.type', 'weight')
		# utils.object.setProperty(data, 'system.capacity.value', 0)

		return [data]

	############################
	#    Template Functions    #
	############################

	# templates.Activities
	def getActivities(self):
		return None

	# templates.ItemDescription
	def getDescription(self, importer):
		text = self.raw_description
		return utils.text.markdownToHtml(text)

	# templates.Identifiable

	# template.ItemType
	def getCategory(self):
		return None

	# template.PhysicalItem

	# templates.EquippableItem

	# templates.Currency
