import util

class ItemDetails:
	'''
		Item details, contains context specific information about the item.
	'''
	def __init__(self, item_dir):
		util._setAttrsFromDir(self, item_dir)


class Item:
	'''
		Primary item object.  Contains data about the item, as well as a potential item.details metadata object.
	'''
	def __init__(self, item_dir = {}):
		util._setAttrsFromDir(self, item_dir)
		
		try:
			self.details = ItemDetails(self.details)
		except AttributeError:
			pass


class Items:
	'''
		Primary items object, use this to query the items API.
	'''
	def __init__(self):
		self.items = {}
		self.name_index = {}


	def getAllItems(self):
		'''
			Populate this object with all existant listings.
		'''
		return self.getItems(util.getAllIds('/v2/items'))


	def getItemByName(self, name):
		'''
			Get the item for a given name.  Requires this object to exist.
			(e.g. getItemByID must have been called; if you don't know the ID,
			getAllItems)

				:param item_id: the item ID to query for.
		'''
		return self.name_index[name]


	def searchItemsByName(self, *search_terms):
		'''
			Get all items that contain the case insensitive terms given as arguments.

				:param search_terms: The terms to search for. (e.g. searchItemByName('tiny', 'snowflake'))
		'''
		found_items = []
		for name in self.name_index:
			if all(search_term.lower() in name.lower() for search_term in search_terms):
				found_items.append(self.name_index[name])
		
		return found_items


	def getItemById(self, item_id):
		'''
			Populate this object with the item for a given ID

				:param item_id: the item ID to query for.
		'''
		return self.getItems([item_id])[0]


	def getItems(self, item_ids):
		'''
			Populate this object with the items for a list of IDs

				:param item_ids: The list of IDs to query for.
		'''
		raw_items = util.idListApiCall('/v2/items?ids=', item_ids)

		for raw_item in raw_items:
			self._indexItem(Item(raw_item))

		return [self.items[int(item_id)] for item_id in item_ids]
		

	def _indexItem(self, item_object):
		'''
			NOTE: INTERNAL FUNCTION.
			Index a given item object.

				:param item_object: the object to index.
		'''
		self.items[item_object.id] = item_object
		self.name_index[item_object.name] = item_object
