import httplib
import json


def apiCall(resource):
	connection = httplib.HTTPConnection("api.guildwars2.com")
	connection.request("GET", resource)

	response = connection.getresponse()

	if response.status != 200:
		connection.close()
		raise Exception("API call failed")

	response_body = response.read()

	connection.close()

	return json.loads(response_body)


