import json
import util
import threading
import util
import sys

class Offer:
	'''
		Contains data on all offers at a given price point.
	'''
	def __init__(self, offer_dir = {}):
		self._dir = offer_dir
		util._setAttrsFromDir(self, offer_dir)

	def __str__(self):
		return str(self._dir)


class ItemListings:
	'''
		Contains all offer listings for a given item, as well as some data on them.
		(mean_buy, max_buy, buy_volume, and the same for sell (except min->max))
	'''
	def __init__(self, listing_dir = {}):
		self._dir = listing_dir
		util._setAttrsFromDir(self, listing_dir)
		
		self.buy_volume = 0
		self.sell_volume = 0

		self.max_buy = 0
		self.min_sell = 99999999

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


	def __str__(self):
		return str({"buy_volume":self.buy_volume, "sell_volume":self.sell_volume, "max_buy":self.max_buy, "mean_buy":self.mean_buy, "min_sell":self.min_sell, "mean_sell":self.mean_sell})


class Listings:
	'''
		Primary listings object, use this to query the listings API.
	'''
	def __init__(self):
		self.listings = {}


	def getAllListings(self):
		'''
			Populate this object with all existant listings.
		'''
		return self.getListings(util.getAllIds('/v2/commerce/listings'))


	def getListingById(self, listing_id):
		'''
			Populate this object with the listings for a given ID

				:param listing_id: the listing ID to query for.
		'''
		return self.getListings([listing_id])[0]


	def getListings(self, listing_ids):
		'''
			Populate this object with the listings for a list of IDs

				:param listing_ids: The list of IDs to query for.
		'''
		raw_listings = util.idListApiCall('/v2/commerce/listings?ids=', listing_ids)

		for raw_listing in raw_listings:
			self._indexListing(ItemListings(raw_listing))

		return [self.listings[int(listing_id)] for listing_id in listing_ids]
		

	def _indexListing(self, listing_object):
		'''
			NOTE: INTERNAL FUNCTION.
			Index a given listing object.

				:param listing_object: the object to index.
		'''
		self.listings[listing_object.id] = listing_object


