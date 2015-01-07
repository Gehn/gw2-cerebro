import util

class Item:
	def __init__(self, item_dir = {}):
		pass

class ItemIndex:
	def __init__(self):
		self.items = {}

	def getAllItems(self):
		raw_items = util.idListApiCall('/v2/items?ids=', util.getAllIds('/v2/items'))

		for raw_item in raw_items:
			self.items[key] = Item(raw_item)

