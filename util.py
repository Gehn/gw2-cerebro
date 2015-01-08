import httplib
import json
from urlparse import urlparse
import threading


def apiCall(resource):
	found_resource = False #To deal with redirects
	url = "api.guildwars2.com"
	protocol = "http"
	while not found_resource:
		print "Getting: ", protocol, url, resource

		if protocol == "https":
			connection = httplib.HTTPSConnection(url)
		else:
			connection = httplib.HTTPConnection(url)

		connection.request("GET", resource)

		response = connection.getresponse()

		if response.status >= 400:
			connection.close()
			raise Exception("API call failed: " + response.reason + " ; " + str(response.status))
		elif response.status == 302:
			parsed_url = urlparse(response.getheader('location'))
			url = parsed_url.netloc
			#resource = parsed_url.path FIXME: Determine if I should have this to some extent.
			protocol = parsed_url.scheme
			print "Redirecting to: ", protocol, url, resource
		elif response.status == 200:
			print "Got response."
			found_resource = True


	response_body = response.read()

	connection.close()

	return json.loads(response_body)










#Inner function.  takes a raw list of listings to query for and returns the response.
def _idListApiCall(resource, listing_list):
	# Convert the listing IDs to a query string and request it
	listings_response = []
	listing_string = ""
	if len(listing_list) > 0:
		for listing_id in listing_list:
			listing_string += str(listing_id) + ','

		listing_string = listing_string[:-1]

		api_string = resource + listing_string
		listings_response = apiCall(api_string)

	return listings_response






def idListApiCall_out(resource, listing_ids, out_list = []):
	'''
		Given an int/stringified int (or list of the above), returns a dir
		of the listings corrosponding to those IDs
		
			:param listing_ids: An int/stringified int (or list) of the item listings desired.
			:param out_list: Simply pass a [] in, it will be populated with the results.
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


	while len(listing_list) != 0:
		listing_batch = listing_list[:BATCH_SIZE]

		out_list += _idListApiCall(resource, listing_batch)

		listing_list = listing_list[BATCH_SIZE:]

	return out_list


#Builds an index of ALL listings.  Be ready for a bit of a wait.
#TODO: Maybe try multiprocessing it? the overhead of starting the other interpreters probably isn't worth it.
def idListApiCall(resource, listing_ids, threaded=True):
	'''
		Given an int/stringified int (or list of the above), returns a dir
		of the listings corrosponding to those IDs

			: param resource: the base resource (e.g. /foo/bar?id= )to query with the ID list
			:param listing_ids: An int/stringified int (or list) of the item listings desired.
	'''
	listing_list = []

	if threaded:
		#Yes I know it can actually start THREADPOOL_SIZE+1 threads, hush.
		THREADPOOL_SIZE=10
		threadpool = []
		for i in range(0, len(listing_ids), len(listing_ids) / THREADPOOL_SIZE):
			thread = threading.Thread( target=idListApiCall_out, kwargs={"resource":resource, "listing_ids":listing_ids[i : ( i + len(listing_ids) / THREADPOOL_SIZE )], "out_list":listing_list} )
			thread.start()
			threadpool.append(thread)
		

		for thread in threadpool:
			thread.join()
	
	else:
		listing_list = idListApiCall_out(listing_ids)

	return listing_list




def getAllIds(resource):
	'''
		Returns a list of all current listing ID's
	'''
	return apiCall(resource)




def setAttrsFromDir(item, attr_dir):
	for var, val in attr_dir.items():
		setattr(item, var, val)


