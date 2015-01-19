#!/usr/bin/env python3

import datetime
import items
import listings
import sys
import time


def logItemData(item, poll_interval=30):
	'''
		This function indefinitely polls the API for a certain items listing data and logs it.

			:param item: The item to gather data on
			:param poll_interval: The number of seconds between polls
	'''
	l = listings.Listings()
	
	prev_time = time.time()
	
	# the number of seconds to trigger on.
	while 1:
		current_time = time.time()
		timestamp = datetime.datetime.now()
		delta = (current_time - prev_time)
	
		if delta >= poll_interval:
			prev_time = current_time
	
			try:
				item_listing = l.getListingById(item.id)
			except Exception as e:
				print(str(e))
				with open("item_errors.log", 'a') as f:
					f.write("timestamp: " + str(timestamp) + " " + str(e) + "\n")
			
			#TODO: make a meaningful Tostring for each of the objects.
			item_data = "timestamp: " + str(timestamp) \
				+ " buy: " + str(item_listing.max_buy) + " sell: " + str(item_listing.min_sell) \
				+ " buy_volume: " + str(item_listing.buy_volume) + " sell_volume: " + str(item_listing.sell_volume) + '\n'
	
			print(item_data)
			with open("item_data.log", 'a') as f:
				f.write(item_data)
		else:
			time.sleep(int(poll_interval - delta))


def alertOnNewItems(callback=None):
	'''
		Truth in advertising.  Polls until there are new items, and then 
		fires the callback, attempting to hand it a list of the new item
		objects found.

			:param callback: the function to call on noticing a change.
	'''
	i = items.Items()
	all_ids = i.getAllIds()

	prev_time = time.time()

	poll_interval = 30
	while 1:
		current_time = time.time()
		timestamp = datetime.datetime.now()
		delta = (current_time - prev_time)
	
		if delta >= poll_interval:
			prev_time = current_time

			new_all_ids = i.getAllIds()

			if set(all_ids) != set(new_all_ids):

				callback(new_all_ids)

				all_ids = new_all_ids
			else:
				print(str(len(all_ids)) + " == " + str(len(new_all_ids)))
				print(str(max(all_ids)) + " , " + str(max(new_all_ids)))
		else:
			time.sleep(int(poll_interval - delta))

			
		

if __name__ == "__main__":

	if "log" in sys.argv:
		i = items.Items()
		i.getAllItems()
		logItemData(i.searchItemsByName('tiny', 'snowflake')[0])
	elif "alert" in sys.argv:
		def foundItemsCallback(new_items):
			found_string = "\nFOUND ITEMS:\n"
			for item in new_items:
				found_string += str(item)
			print(found_string)
			with open("new_items.log", 'a') as f:
				f.write(found_string)
				
		alertOnNewItems(foundItemsCallback)
