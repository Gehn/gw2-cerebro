import collections
defaultdict = collections.defaultdict
import json
import util
import threading
import util
import sys
import time

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

		self.margin = 0

		self.volume_margin = 0

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

		#Calculate the margin.
		delta = self.min_sell - self.max_buy
		fee = (self.min_sell - 1) * .15
		self.margin = (delta - fee) / (self.max_buy + 1)

		#Calculate volume margin
		self.volume_margin = float("inf")
		if self.sell_volume:		
			self.volume_margin =  self.buy_volume / self.sell_volume 


	def __str__(self):
		return str({"buy_volume":self.buy_volume, "sell_volume":self.sell_volume, "max_buy":self.max_buy, "mean_buy":self.mean_buy, "min_sell":self.min_sell, "mean_sell":self.mean_sell})


#TODO: MAKE CACHED VS UNCACHED VERSIONS.
class Listings:
	'''
		Primary listings object, use this to query the listings API.
	'''
	def __init__(self, listings=[]):
		self.listings = {}
	
		for listing in listings:
			self._indexListing(listing)


	def getAllListings(self, use_cache=False):
		'''
			Populate this object with all existant listings.
		'''
		return self.getListingsById(self.getAllIds(), use_cache)


	def getListingById(self, listing_id, use_cache=False):
		'''
			Populate this object with the listings for a given ID

				:param listing_id: the listing ID to query for.
		'''
		return self.getListingsById([listing_id], use_cache)[0]


	def getListingsById(self, listing_ids, use_cache=False):
		'''
			Populate this object with the listings for a list of IDs

				:param listing_ids: The list of IDs to query for.
		'''
		# This section handles getting any cached entries, and pruning the query id list if so
		cached_results = []
		if use_cache:
			cached_ids = [listing_id for listing_id in listing_ids if int(listing_id) in self.listings]
			cached_results = [self.listings[int(listing_id)] for listing_id in cached_ids]
			listing_ids = list(set(listing_ids) - set(cached_ids))

		# This section gets any ids in the id list from the API.
		if listing_ids:
			raw_listings = util.idListApiCall('/v2/commerce/listings?ids=', listing_ids)

			for raw_listing in raw_listings:
				self._indexListing(ItemListings(raw_listing))

		return cached_results + [self.listings[int(listing_id)] for listing_id in listing_ids if int(listing_id) in self.listings]

		
	def getAllIds(self):
		'''
			Returns a list of all numerical listing IDs
		'''
		return util.getAllIds('/v2/commerce/listings')


	def _indexListing(self, listing_object):
		'''
			NOTE: INTERNAL FUNCTION.
			Index a given listing object.

				:param listing_object: the object to index.
		'''
		self.listings[listing_object.id] = listing_object


	#FIXME: fix the util funtion then use it under this.
	def getApproximateItemVolatility(self, item_ids, delay=10):
		'''
			NOTE: this is a concept; only works on certain items with high enough volatility.
			To be rewritten and deprecated.

			Query multiple times to observe how volume changes and return
			a metric for volatility derived from this. 

				:param item_ids: List of item ids to query. (also accepts single id)
				:param delay: delay between each query.
		'''

		if item_ids.__class__ != [].__class__:
			item_ids = [item_ids]

		def inner_defaultdict():
			return defaultdict(int)

		volatility_map = defaultdict(inner_defaultdict) #id:{net_buy, net_sell, abs_buy, abs_sell}
		iterations = 30

		listings = {listing.id:listing for listing in self.getListingsById(item_ids)}
		for iteration in range(0, iterations):
			time.sleep(delay)
			new_listings = {listing.id:listing for listing in self.getListingsById(item_ids)}
			for listing_id, listing in listings.items():
				new_listing = new_listings[listing_id]
				buy_delta = listing.buy_volume - new_listing.buy_volume
				sell_delta = listing.sell_volume - new_listing.sell_volume

				volatility_map[listing_id]["net_buy"] += buy_delta
				volatility_map[listing_id]["net_sell"] += sell_delta
				volatility_map[listing_id]["abs_buy"] += abs(buy_delta)
				volatility_map[listing_id]["abs_sell"] += abs(sell_delta)

		for data in volatility_map.values():
			for name, metric in data.items():
				data[name] = metric / iterations


		return volatility_map

	def searchListingsByLambda(self, listing_filter):
		'''
			Query all listings by a certain filter, a callable that takes the listing as an argument,
			returns true if it should accept the listing, false if not.

				:param listing_filter: callable taking one argument of the listing object to be examined, returns boolean.
		'''
		found_listings = []
		for listing in self.listings.values():
			if listing_filter(listing):
				found_listings.append(listing)

		return found_listings
				
