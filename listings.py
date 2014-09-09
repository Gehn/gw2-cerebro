import json
import util


class listing:
	def __init__(self, listing_dir = {}):
		self.listings = None
		self.unit_price = None
		self.quantity = None

		if listing_dir and listing_dir != {}:
			self.listings = listing_dir["listings"]
			self.unit_price = listing_dir["unit_price"]
			self.quantity = listing_dir["quantity"]

class listingsForID:
	def __init__(self, listing_dir = {}):
		self._id = None
		self.buys = None

		if listing_dir and listing_dir != {}:
			self._id = listing_dir["id"]
			self.buys = listing_dir["buys"]



