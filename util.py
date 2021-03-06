import http.client as httplib
import json
from urllib.parse import urlparse
import threading
import logging
import sys
import math
import time
import datetime
import base64
import codecs
import struct
import time

formatter = logging.Formatter('%(levelname)s : %(asctime)s : %(message)s')
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(0)
handler.setFormatter(formatter)
logger = logging.getLogger()
logger.setLevel(0)
logger.addHandler(handler)

logger.info('Logging enabled.')


def apiCall(resource):
	'''
		Core API call to the api.guildwars2.com api. Simply makes an http
		request and returns the un-jsonified response.

			:param resource: the path (e.g. /v2/items) to query for.
	'''
	found_resource = False #To deal with redirects
	parsed_response = False #To deal with invalid responses.

	retries = 0 # How many retries have we gone through thus far.
	retry_threshold = 5 # For transient errors
	retry_delay = 1 # Seconds

	url = "api.guildwars2.com"
	protocol = "https"

	while not found_resource and not parsed_response:
		logger.debug("Getting: " + str(protocol) + str(url) + str(resource))

		if protocol == "https":
			connection = httplib.HTTPSConnection(url)
		else:
			connection = httplib.HTTPConnection(url)

		connection.request("GET", resource)

		response = connection.getresponse()

		if response.status >= 500 and retries < retry_threshold:
			logger.error("Retrying due to potentially transient API failure: " + response.reason + " ; " + str(response.status))
			retries += 1
			time.sleep(retry_delay)
			continue
		elif response.status >= 400:
			connection.close()
			logger.error("API call failed: " + response.reason + " ; " + str(response.status))
			raise Exception("API call failed: " + response.reason + " ; " + str(response.status))
		elif response.status == 302:
			parsed_url = urlparse(response.getheader('location'))
			url = parsed_url.netloc
			#resource = parsed_url.path FIXME: Determine if I should have this to some extent.
			protocol = parsed_url.scheme
			logger.debug("Redirecting to: " + str(protocol) + str(url) + str(resource))
			continue
		elif 200 <= response.status < 300 :
			logger.debug("Got response.")
			found_resource = True
		else:
			logger.error("Unspecified response: " + str(response.status))


		response_body = response.read()
		try:
			data = json.loads(response_body.decode())
			parsed_response = True
		except Exception as e: #Known to be value error; but that came out of nowhere, so being a bit generous here.
			logger.error("Json parsing failure for " + str(resource) + " : " + str(e))
			parsed_response = False


	connection.close()

	return data



def _idListApiCall(resource, id_list):
	'''
		NOTE: INTERNAL FUNCTION
		Makes a call to the API appending a list of stringified values comma seperated.

			:param resource: the path (e.g. /v2/items?ids=) to query for.
			:param id_list: The list of ids to query for. 
	'''
	# Convert the listing IDs to a query string and request it
	api_response = []
	id_list_string = ""
	if len(id_list) > 0:
		for each_id in id_list:
			id_list_string += str(each_id) + ','

		id_list_string = id_list_string[:-1]

		api_string = resource + id_list_string
		api_response = apiCall(api_string)

	return api_response



def idListApiCall_out(resource, id_list, out_list = []):
	'''
		Given an int/stringified int (or list of the above), returns a dir
		of the listings corrosponding to those IDs
		
			:param resource: the path (e.g. /v2/items?ids=) to query for.
			:param id_list: An int/stringified int (or list) of the item listings desired.
			:param out_list: Simply pass a [] in, it will be populated with the results.
	'''
	BATCH_SIZE = 200 #Can get pushed higher, but it gets iffy.
	# Does nastiness to allow many sorts of valid id_list types.
	# e.g. int, stringified int, list of ints and list of stringified ints.
	each_id = None
	parsed_id_list = []
	try:
		#If it's an int we just cram it in the string
		each_id = int(id_list)
		parsed_id_list = [each_id]
	except:
		#If it's a list of ints we build a comma seperated list
		for each_id in id_list:
			int(each_id)
			parsed_id_list.append(each_id)


	while len(parsed_id_list) != 0:
		id_list_batch = parsed_id_list[:BATCH_SIZE]

		out_list += _idListApiCall(resource, id_list_batch)

		parsed_id_list = parsed_id_list[BATCH_SIZE:]

	return out_list


#Builds an index of ALL listings.  Be ready for a bit of a wait.
#TODO: Maybe try multiprocessing it? the overhead of starting the other interpreters probably isn't worth it.
def idListApiCall(resource, id_list, threaded=True, cache_timeout=0):
	'''
		Given an int/stringified int (or list of the above), returns a dir
		of the listings corrosponding to those IDs

			:param resource: the path (e.g. /v2/items?ids=) to query for.
			:param id_list: An int/stringified int (or list) of the item listings desired.
	'''
	out_list = []

	if threaded:
		#Yes I know it can actually start THREADPOOL_SIZE+1 threads, hush.
		THREADPOOL_SIZE=10
		threadpool = []
		ids_per_thread = math.ceil(len(id_list) / THREADPOOL_SIZE)
		for i in range(0, len(id_list), ids_per_thread):
			thread = threading.Thread( target=idListApiCall_out, kwargs={"resource":resource, "id_list":id_list[i : math.ceil( i + len(id_list) / THREADPOOL_SIZE )], "out_list":out_list} )
			thread.start()
			threadpool.append(thread)
		

		for thread in threadpool:
			thread.join()
	
	else:
		out_list = idListApiCall_out(resource, id_list)

	return out_list




def getAllIds(resource):
	'''
		Returns a list of all current listing ID's
	'''
	return apiCall(resource)


def getSecretListings(item_api, listing_api):
	'''
		Get all items that have listings but no index in the public items API
	'''
	
	item_ids = item_api.getAllIds()
	listing_ids = listing_api.getAllIds()

	return list(set(listing_ids) - set(item_ids))


def makeItemCode(item_id, num_items=1):
	'''
		Generate ingame code from item ID.

			:param item_id: the item_id to codify (in int or string form)
			:param num_items: the number of items to simulate in the code.
	'''
	headers = struct.pack('<b', 2) + struct.pack('<b', num_items)
	hex_item_id = struct.pack('<i', int(item_id))

	return "[&" + base64.b64encode(headers + hex_item_id).decode('utf-8') + "]"


def makeItemCodes(item_ids):
	'''
		Generate item codes from a list of IDs

			:param item_ids: the list of ids to generate codes for.
	'''
	return [makeItemCode(item_id) for item_id in item_ids]


def _setAttrsFromDir(item, attr_dir):
	'''
		NOTE: INTERNAL FUNCTION
		Helper function for parsing an API response into a class automagically.
	'''
	for var, val in attr_dir.items():
		setattr(item, var, val)



def _determineMaxRequestBatchSize():
	'''
		NOTE: INTERNAL FUNCTION
		Little helper function, tells you what the API limits you to in terms of ID's in a single request,
		does so by binary search.  At last run, the number was 200.
	'''
	ids = getAllIds('/v2/items')

	#Arbitrary start point; much higher than current limit.
	#(But given a guess that the real number is 200+some; this should binary search the target nicely)
	previous_batch_size = 1000
	batch_size = 800
	halt = False
	while not halt:
		tmp_batch_size = batch_size
		try:
			logger.debug("Trying batch size: " + str(batch_size))

			_idListApiCall('/v2/items?ids=', ids[:batch_size])

			if previous_batch_size < batch_size:
				batch_size += (batch_size - previous_batch_size)
			elif previous_batch_size > batch_size:
				batch_size += (previous_batch_size - batch_size) / 2
			else:
				halt = True
		except Exception as e:
			logger.exception(e)

			if previous_batch_size > batch_size:
				batch_size -= (previous_batch_size - batch_size)
			elif previous_batch_size < batch_size:
				batch_size -= (batch_size - previous_batch_size) / 2
			else:
				batch_size -= 1

			if batch_size <= 0:
				halt = True

		previous_batch_size = tmp_batch_size

	return batch_size


#TODO: variance as well?
def _determineApiDataRefreshRate(sample_id=19697): 
	'''
		NOTE: INTERNAL FUNCTION
		Another strange helper, tries to determine some data about the rate at which API data is refreshing,
		so that you can most find an optimal rate to query it without going overboard.  

		NOTE2:
		This may also tell us some interesting things about the rate at which data is moving, since pragmatically the refresh
		rate has not been consistent; meaning it's likely some sort of push based system, perhaps on transaction
		volume in the interim?  It would be interesting to experiment with, but I'm rambling.

			:param sample_id: What item should be polled.  Copper ore used as an index by default because yes.
	'''
	num_trials = 1000
	trial_delay = 1

	prev_sell_quantity = 0
	prev_buy_quantity = 0
	interval_start = None
	discarded_first_interval = False #We may be coming in "halfway through"
	intervals = []
	max_interval = datetime.timedelta()
	min_interval = datetime.timedelta(days=9999)
	for i in range(0, num_trials):
		time.sleep(trial_delay)

		interval_end = datetime.datetime.now()
		ret = apiCall("/v2/commerce/prices?ids=" + str(sample_id)) # copper ore, it's always moving.
		
		sell_quantity = ret[0]["sells"]["quantity"]
		buy_quantity = ret[0]["buys"]["quantity"]

		if sell_quantity != prev_sell_quantity or buy_quantity != prev_buy_quantity:
			#We need to get the first data first; going from start->first value doesn't count.
			if interval_start:
				#And even then; we still need to throw out our first "real" interval.
				if discarded_first_interval:
					interval = interval_end - interval_start
					intervals.append(interval)
					logger.debug("Found interval: " + str(interval) + " In trial: " + str(i))

					if interval > max_interval:
						logger.debug("Found new max interval")
						max_interval = interval
					if interval < min_interval:
						logger.debug("Found new min interval")
						min_interval = interval
				else:
					discarded_first_interval = True

			prev_sell_quantity = sell_quantity
			prev_buy_quantity = buy_quantity

			interval_start = interval_end

	print(intervals)
	total_delta = datetime.timedelta(0,0,0)
	for interval in intervals:
		total_delta += interval
	if len(intervals) > 0:
		average_interval = total_delta / len(intervals)

	return {"mean": average_interval, "min": min_interval, "max": max_interval}


def zipItemsAndListings(items, listings):
	'''
		Associate the items and listings sharing IDs in a {uid:{item:item,listing:listing}} datastructure.
		Only adds to the zipped list if present in both lists.

			:param items: the list of items to zip.
			:param listings: the list of listings to zip.
	'''
	listing_map = {listing.id:listing for listing in listings}

	results = {}
	for item in items:
		if item.id in listing_map:
			listing = listing_map[item.id]
			results[item.name + '.' + str(item.id)] = {"item":item, "listing":listing}

	return results


def zipObjectsByField(iterable_a, iterable_b, field):
	'''
		More generic object zipper.  Takes two iterables and zips the contents
		along a single field.
		They must not be of the same length, only objects which have a zipped
		partner are returned.

			:param iterable_a: The first iterable of objects
			:param iterable_b: The second iterable of objects
			:param field: The field to zip on
	'''
	zipped_map = []

	field_index = {getattr(item, field):item for item in iterable_a}

	for item in iterable_b:
		if getattr(item, field) in field_index:
			joined_item = field_index[getattr(item, field)]
			zipped_map[iterable_a] = iterable_b

	return zipped_map
if __name__ == "__main__":
	print(getItemCode(29952))
