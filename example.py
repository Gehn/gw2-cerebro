import items
import listings
import datetime


def logItemData(item, epsilon=30):
	'''
		This function indefinitely polls the API for a certain items listing data and logs it.

			:param item: The item to gather data on
			:param epsilon: The number of seconds between polls
	'''
	l = listings.Listings()
	
	prev_time = datetime.datetime.now()
	
	# the number of seconds to trigger on.
	while 1:
		current_time = datetime.datetime.now()
		delta = (current_time - prev_time)
	
		if delta >= datetime.timedelta(seconds=epsilon):
			prev_time = current_time
	
			try:
				item_listing = l.getListingById(item.id)
			except Exception as e:
				print(str(e))
				with open("item_errors.log", 'a') as f:
					f.write("timestamp: " + str(current_time) + " " + str(e) + "\n")
			
			#TODO: make a meaningful Tostring for each of the objects.
			item_data = "timestamp: " + str(current_time) \
				+ " buy: " + str(item_listing.max_buy) + " sell: " + str(item_listing.min_sell) \
				+ " buy_volume: " + str(item_listing.buy_volume) + " sell_volume: " + str(item_listing.sell_volume) + '\n'
	
			print(item_data)
			with open("item_data.log", 'a') as f:
				f.write(item_data)
	
			

if __name__ == "__main__":
	i = items.Items()
	i.getAllItems()
	logItemData(i.searchItemsByName('tiny', 'snowflake')[0])
