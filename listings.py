import json
import util
import threading
import util

class Offer:
	def __init__(self, item_dir):
		util.setAttrsFromDir(self, item_dir)


class ItemListings:
	def __init__(self, item_dir = {}):
		util.setAttrsFromDir(self, item_dir)
		
		self.buy_volume = 0
		self.sell_volume = 0

		self.max_buy = 0
		self.min_sell = 0

		self.mean_buy = 0
		self.median_buy = 0
		self.mode_buy = 0

		self.mean_sell = 0
		self.median_sell = 0
		self.mode_sell = 0

		buy_objects = []
		#enumerate buys.
		for raw_buy in self.buys:
			#Create a offer object for each one.
			buy = Offer(raw_buy)
			buy_objects.append(buy)

			#Compute the max buy, rolling.
			if buy.unit_price > self.max_buy:
				self.max_buy = buy.unit_price

			#Compute the first half of the mean, rolling.
			self.mean_buy += buy.unit_price * buy.quantity

			# TODO: an interesting thought would be deriving volume from listing count.
			self.buy_volume += buy.quantity
		self.buys = buy_objects

		sell_objects = []
		#Enumerate sells.
		for raw_sell in self.sells:
			#Create a offer object for each one.
			sell = Offer(raw_sell)
			sell_objects.append(sell)

			#Compute the min sell, rolling.
			if sell.unit_price < self.min_sell:
				self.min_sell = sell.unit_price

			#Compute the first half of the mean, rolling.
			self.mean_sell += sell.unit_price * sell.quantity

			self.sell_volume += sell.quantity

		self.sells = sell_objects

		#Calculate the second halves of the means now that we have all listings.
		if self.sell_volume > 0:
			self.mean_sell /= self.sell_volume

		if self.buy_volume > 0:
			self.mean_buy /= self.buy_volume

		#TODO: Calculate the medians.  remember that each listing has multiple quantity.



class Listings:
	def __init__(self):
		self.listings = {}


	def getAllListings(self):
		return self.getListings(util.getAllIds('/v2/commerce/listings'))


	def getItemByName(self, name):
		return self.name_index[name]


	def getItemById(self, item_id):
		return getItems([item_id])[0]


	def getListings(self, listing_ids):
		raw_listings = util.idListApiCall('/v2/commerce/listings?ids=', listing_ids)

		for raw_listing in raw_listings:
			self._indexListing(ItemListings(raw_listing))

		return [self.listings[int(listing_id)] for listing_id in listing_ids]
		

	def _indexListing(self, listing_object):
		self.listings[listing_object.id] = listing_object


