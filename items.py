import util

class ItemDetails:
	def __init__(self, item_dir):
		util.setAttrsFromDir(self, item_dir)


class Item:
	def __init__(self, item_dir = {}):
		util.setAttrsFromDir(self, item_dir)
		
		try:
			self.details = ItemDetails(self.details)
		except AttributeError:
			pass


class ItemIndex:
	def __init__(self):
		self.items = {}
		self.name_index = {}


	def getAllItems(self):
		return self.getItems(util.getAllIds('/v2/items'))


	def getItemByName(self, name):
		return self.name_index[name]


	def getItemById(self, item_id):
		return getItems([item_id])[0]


	def getItems(self, item_ids):
		raw_items = util.idListApiCall('/v2/items?ids=', item_ids)

		for raw_item in raw_items:
			self._indexItem(Item(raw_item))

		return [self.items[int(item_id)] for item_id in item_ids]
		

	def _indexItem(self, item_object):
		self.items[item_object.id] = item_object
		self.name_index[item_object.name] = item_object
