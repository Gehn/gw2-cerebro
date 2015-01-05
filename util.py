import httplib
import json
from urlparse import urlparse


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


