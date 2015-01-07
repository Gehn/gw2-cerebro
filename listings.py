import json
import util
import threading


class Offer:
	def __init__(self, listing_dir = {}):
		self.listings = 0
		self.unit_price = 0
		self.quantity = 0

		if listing_dir and listing_dir != {}:
			self.listings = listing_dir["listings"]
			self.unit_price = listing_dir["unit_price"]
			self.quantity = listing_dir["quantity"]


class ItemListing:
	def __init__(self, listing_dir = {}):
		self._id = None
		self.buys = []
		self.sells = []

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

		if listing_dir and listing_dir != {}:
			self._id = listing_dir["id"]

			#enumerate buys.
			for listing_raw in listing_dir["buys"]:
				#Create a offer object for each one.
				offer = Offer(listing_raw)
				self.buys.append(offer)

				#Compute the max buy, rolling.
				if offer.unit_price > self.max_buy:
					self.max_buy = offer.unit_price

				#Compute the first half of the mean, rolling.
				self.mean_buy += offer.unit_price * offer.quantity

				# TODO: an interesting thought would be deriving volume from listing count.
				self.buy_volume += offer.quantity


			#Enumerate sells.
			for listing_raw in listing_dir["sells"]:
				#Create a offer object for each one.
				offer = Offer(listing_raw)
				self.sells.append(offer)

				#Compute the min sell, rolling.
				if offer.unit_price < self.min_sell:
					self.min_sell = offer.unit_price

				#Compute the first half of the mean, rolling.
				self.mean_sell += offer.unit_price * offer.quantity

				self.sell_volume += offer.quantity

			#Calculate the second halves of the means now that we have all listings.
			if self.sell_volume > 0:
				self.mean_sell /= self.sell_volume

			if self.buy_volume > 0:
				self.mean_buy /= self.buy_volume

			#TODO: Calculate the medians.  remember that each listing has multiple quantity.


class Market:
	def __init__(self):
		self.item_listings = {}


	def clearCache(self):
		self.item_listings = {}


	#Inner function.  takes a raw list of listings to query for and returns the response.
	def _getListingsByList(self, listing_list):
		# Figure out what is in the cache.
		cached_listing_list = []
		trimmed_listing_list = []
		for listing in listing_list:
			try:
				if self.item_listings[listing] == None:
					trimmed_listing_list.append(listing)
				else:
					cached_listing_list.append(listing)
			except:
				pass

		#Populate from the cache.
		listings_by_id_index = {}
		for listing in cached_listing_list:
			listings_by_id_index[listing] = self.item_listings[listing]

		# Convert the uncached listing IDs to a query string and request it
		listings_response = []
		listing_string = ""
		if len(trimmed_listing_list) > 0:
			for listing_id in trimmed_listing_list:
				listing_string += str(listing_id) + ','
	
			listing_string = listing_string[:-1]
	
			api_string = '/v2/commerce/listings?ids=' + listing_string
			listings_response = util.apiCall(api_string)

		#Parse the response.
		for listings_by_id_dict in listings_response:
			listings_by_id = ItemListing(listings_by_id_dict)
			listings_by_id_index[listings_by_id._id] = listings_by_id

			self.item_listings[int(listings_by_id._id)] = listings_by_id
			
		return listings_by_id_index



	def getListings_out(self, listing_ids, out_dir):
		'''
			Given an int/stringified int (or list of the above), returns a dir
			of the listings corrosponding to those IDs
		
				:param listing_ids: An int/stringified int (or list) of the item listings desired.
				:param out_dir: Simply pass a {} in, it will be populated with the results.
		'''
		BATCH_SIZE = 200 #Can get pushed higher, but it gets iffy. FIXME: narrow down better.

		# Does nastiness to allow many sorts of valid listing_ids types.
		# e.g. int, stringified int, list of ints and list of stringified ints.
		listing_id = None
		listing_list = []
		try:
			#If it's an int we just cram it in the string
			listing_id = int(listing_ids)
			listing_list = [listing_id]
		except:
			#If it's a list of ints we build a comma seperated list
			for listing_id in listing_ids:
				int(listing_id)
				listing_list.append(listing_id)


		accumulated_index = {}
		while len(listing_list) != 0:
			listing_batch = listing_list[:BATCH_SIZE]

			index = self._getListingsByList(listing_batch)

			listing_list = listing_list[BATCH_SIZE:]

			for (key, value) in index.items():
				accumulated_index[key] = value

				if out_dir != None:
					out_dir[key] = value

		return accumulated_index


	def getListings(self, listing_ids):
		'''
			Given an int/stringified int (or list of the above), returns a dir
			of the listings corrosponding to those IDs

				:param listing_ids: An int/stringified int (or list) of the item listings desired.
		'''
		return self.getListings_out(listing_ids, None)


	#Builds an index of ALL listings.  Be ready for a bit of a wait.
	#TODO: Maybe try multiprocessing it? the overhead of starting the other interpreters probably isn't worth it.
	def getAllListings(self, threaded=True):

		listing_ids = self.getAllListingIDs()[:1000]
		listing_index = {}

		if threaded:
			#Yes I know it can actually start THREADPOOL_SIZE+1 threads, hush.
			THREADPOOL_SIZE=10
			threadpool = []
			for i in range(0, len(listing_ids), len(listing_ids) / THREADPOOL_SIZE):
				thread = threading.Thread( target=self.getListings_out, kwargs={"listing_ids":listing_ids[i : ( i + len(listing_ids) / THREADPOOL_SIZE )], "out_dir":listing_index} )
				thread.start()
				threadpool.append(thread)
			

			for thread in threadpool:
				thread.join()
		
		else:
			listing_index = self.getListings(listing_ids)

		return listing_index




	def getAllListingIDs(self):
		'''
			Returns a list of all current listing ID's
		'''
		for listing_id in util.apiCall('/v2/commerce/listings'):
			if int(listing_id) not in self.item_listings:
				self.item_listings[int(listing_id)] = None

		return self.item_listings.keys()



