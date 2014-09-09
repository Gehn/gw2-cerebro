import util
import threading


class Listing:
	def __init__(self, listing_dir = {}):
		self.listings = None
		self.unit_price = None
		self.quantity = None

		if listing_dir and listing_dir != {}:
			self.listings = listing_dir["listings"]
			self.unit_price = listing_dir["unit_price"]
			self.quantity = listing_dir["quantity"]

class ListingsByID:
	def __init__(self, listing_dir = {}):
		self._id = None
		self.buys = None
		self.sells = None

		if listing_dir and listing_dir != {}:
			self._id = listing_dir["id"]
			self.buys = [Listing(l) for l in listing_dir["buys"]]
			self.sells = [Listing(l) for l in listing_dir["sells"]]


#Inner function.  takes a raw list of listings to query for and returns the response.
def _queryListingsByIDList(listing_list):
	listing_string = ""
	if len(listing_list) > 0:
		for listing_id in listing_list:
			listing_string += str(listing_id) + ','

		listing_string = listing_string[:-1]

	api_string = '/v2/commerce/listings?ids=' + listing_string
	listings_response = util.apiCall(api_string)

	listings_by_id_index = {}
	for listings_by_id_dict in listings_response:
		listings_by_id = ListingsByID(listings_by_id_dict)
		listings_by_id_index[listings_by_id._id] = listings_by_id
		

	return listings_by_id_index



#Takes an int, string of an int, or enumerable of ints (or ints in strings yadda yadda)
#returns a dictionary in the form of {id:listingsById}
#Also populates the out_dir directory ({}) that you pass in to it.  For use in threaded applications.
def queryListingsByID_out(listing_ids, out_dir):
	BATCH_SIZE = 300

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

		index = _queryListingsByIDList(listing_batch)

		listing_list = listing_list[BATCH_SIZE:]

		for (key, value) in index.items():
			accumulated_index[key] = value

			if out_dir != None:
				#print "Adding:", key, " ", value
				out_dir[key] = value

	#print "Found:", len(accumulated_index)
	return accumulated_index


#Takes an int, string of an int, or enumerable of ints (or ints in strings yadda yadda)
#returns a dictionary in the form of {id:listingsById}
def queryListingsByID(listing_ids):
	return queryListingsByID_out(listing_ids, None)


#Returns a list of all current listing ID's
def queryListings():

	return util.apiCall('/v2/commerce/listings')



#Builds an index of ALL listings.  Be ready for a bit of a wait.
#TODO: Maybe try multiprocessing it? the overhead of starting the other interpreters probably isn't worth it.
def deepQueryListings(threaded=True):

	listing_ids = queryListings()[:1000]
	listing_index = {}

	if threaded:
		#Yes I know it can actually start THREADPOOL_SIZE+1 threads, hush.
		THREADPOOL_SIZE=10
		threadpool = []
		for i in range(0, len(listing_ids), len(listing_ids) / THREADPOOL_SIZE):
			thread = threading.Thread( target=queryListingsByID_out, kwargs={"listing_ids":listing_ids[i : ( i + len(listing_ids) / THREADPOOL_SIZE )], "out_dir":listing_index} )
			thread.start()
			threadpool.append(thread)
		

		for thread in threadpool:
			thread.join()
	
	else:
		listing_index = queryListingsByID(listing_ids[-1000:])

	return listing_index

