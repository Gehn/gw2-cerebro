#!/usr/bin/env python3

import datetime
import items
import listings
import signal
import sys
import threading
import time
from util import logger

class WatcherTrigger:
	def __init__(self, \
			item_ids=[], \
			run_interval=None, \
			buy_ceiling=None, \
			sell_floor=None, \
			sell_volume_ceiling=None, \
			sell_volume_floor=None, \
			buy_volume_ceiling=None, \
			buy_volume_floor=None):

		self.item_ids = item_ids

		#TODO: if you made this a map of id:threshold object, one trigger object could hold all permutations.
		self.run_interval = run_interval
		self._last_run = None

		self.buy_ceiling = buy_ceiling
		self.sell_floor = sell_floor
		self.sell_volume_ceiling = sell_volume_ceiling
		self.sell_volume_floor = sell_volume_floor
		self.buy_volume_ceiling = buy_volume_ceiling
		self.buy_volume_floor = buy_volume_floor


	def run(self, context):
		item_listings = context.listing_api.getListingsById(self.item_ids)

		if self.run_interval:
			curr_time = time.time()
			if not self._last_run:
				self._last_run = curr_time

			elif curr_time - self._last_run >= self.run_interval:
				self._last_run = curr_time
				return item_listings

		items_of_interest = []

		for item_listing in item_listings:
			if (self.buy_ceiling and item_listing.max_buy > self.buy_ceiling) \
			or (self.sell_floor and item_listing.min_sell < self.sell_floor) \
			or (self.sell_volume_ceiling and item_listing.sell_volume > self.sell_volume_ceiling) \
			or (self.sell_volume_floor and item_listing.sell_volume < self.sell_volume_floor) \
			or (self.buy_volume_ceiling and item_listing.buy_volume > self.buy_volume_ceiling) \
			or (self.buy_volume_floor and item_listing.buy_volume < self.buy_volume_floor):
				items_of_interest.append(item_listing)

		return items_of_interest


	def __call__(self, context):
		return self.run(context)


class WatcherThread:
	'''
		This is the mysterious "context" object that gets passed around to everything.  It is simply
		a bucket for a thread running the callable at the heart of the watcher, as well as being a bucket
		for any data that callable might need, including what should happen if the event being
		watched for occurs.
	'''
	def __init__(self, target, waiters = [], item_api = None, listing_api = None):
		'''
			Initialize the thread.

				:param target: the callable object to be invoked when you call start(). (must take a context object)
				:param waiters: A list of callable objects to be run if the watcher triggers them. (must each take a data object)
				:param item_api: an instance of the items api to utilize.
				:param listing_api: an instance of the listings api to utilize.
		'''
		self.poll_interval = 30

		if not item_api:
			item_api = items.Items()
		if not listing_api:
			listing_api = listings.Listings()

		self.item_api = item_api
		self.listing_api = listing_api

		self.halt = False

		self._thread = None
		self._target = target
		self._waiters = waiters


	def start(self):
		'''
			Start the thread's activity.
		'''
		# Saw no reason to do it like real threading with a seperate run method, at least for now.
		_thread = threading.Thread(None, self._target, args=(self,))
		_thread.start()


	#TODO: I wonder if waiters are better tied to triggers as callbacks.
	def runWaiters(self, data):
		'''
			Runs each of the functions declared as waiters (to run when the target triggers them)
			passing the data parameter as a single argument.

				:param data: any arbitrary data to pass to the waiters.
		'''
		for waiter in self._waiters:
			try:
				waiter(data)
			except Exception as e:
				logger.exception(e)


	#TODO: this may be able to be pulled entirely out of this. (Unless I put the timed retrying stuff in here, which may be smarter)
	def setPollInterval(self, new_poll_interval):
		'''
			Set the interval (in seconds) that this watcher should poll at.
		'''
		self.poll_interval = new_poll_interval


class Watcher:
	def __init__(self):
		'''
			Initialize the watcher controller.  From here you can create new watch tasks.
		'''
		self.default_poll_interval = 30
		self.watcher_threads = []

		self.item_api = items.Items()
		self.listing_api = listings.Listings()


	def _createWatcherThread(self, target, waiters=None, item_api = None, listing_api = None):
		'''
			Internal function.  Creates a single watcher thread objects with the specified
			parameters and returns it, after starting it.

				:param target: The target callable object to run within the thread. (must take a context object)
				:param waiters: A list of callable objects to be run if the watcher triggers them. (must each take a data object)
				:param item_api: an instance of the items api to utilize.
				:param listing_api: an instance of the listings api to utilize.
		'''
		if not item_api:
			item_api = self.item_api
		if not listing_api:
			listing_api = self.listing_api

		new_watcher_thread = WatcherThread(target, waiters, item_api, listing_api)
		new_watcher_thread.setPollInterval(self.default_poll_interval)
		self.watcher_threads.append(new_watcher_thread)
		new_watcher_thread.start()

		return target


	def setDefaultPollInterval(self, new_default_poll_interval):
		'''
			Set the interval (in seconds) that created watcher tasks should poll at,
			unless explicitely overridden.
		'''
		self.default_poll_interval = new_default_poll_interval


	def watchListings(self, trigger, callback):
		pass #TODO: Implement or deprecate.


	def batchWatchListings(self, trigger_callback_tuple_list):
		def pollTriggers(context):
			while not context.halt:
				try_again_interval = None
				for triggers, callbacks in trigger_callback_tuple_list:
					data = []
					for trigger in triggers:
						data += trigger(context)

						if trigger.run_interval != None and (try_again_interval == None or trigger.run_interval < try_again_interval):
							try_again_interval = trigger.run_interval

					if data != []:
						for callback in callbacks:
							callback(data)

				if try_again_interval == None:
					try_again_interval = context.poll_interval

				time.sleep(try_again_interval)


		new_watcher_thread = self._createWatcherThread(pollTriggers)
		return new_watcher_thread


	def _watchForNewIds(self, id_query, onChangeFunctions):
		'''
			Internal function, Creates a watcher for if new item IDs appear as returned from a given query.

				:param id_query: A callable object that returns a list which can be set-diffed against later iterations of itself.
				:param onChangeFunctions: A list of callable objects to call when a change is noticed. (must each take a data object)
		'''
		#TODO: this might be a good place of where to override the trigger run routine, and use triggers everywhere.
		def watchForNewItemsLoop(context):
			all_ids = id_query()

			prev_time = time.time()

			while not context.halt:
				current_time = time.time()
				delta = (current_time - prev_time)
			
				if delta >= context.poll_interval:
					prev_time = current_time

					new_all_ids = id_query()

					if set(all_ids) != set(new_all_ids):
						print("found distinct sets: " + str(len(all_ids)) + "," + str(len(new_all_ids)))
						context.runWaiters(set(new_all_ids) - set(all_ids))

						all_ids = new_all_ids
				else:
					time.sleep(int(context.poll_interval - delta))


		#TODO: can maybe turn this bit into a decorator?
		new_watcher_thread = self._createWatcherThread(watchForNewItemsLoop, onChangeFunctions)
		return new_watcher_thread


	def watchForNewItems(self, onChangeFunctions):
		'''
			Creates a watcher for if new item IDs appear in the items API.

				:param onChangeFunctions: A list of callable objects to call when a change is noticed. (must each take a data object)
		'''
		return self._watchForNewIds(self.item_api.getAllIds, onChangeFunctions)


	def watchForNewListings(self, onChangeFunctions):
		'''
			Creates a watcher for if new item IDs appear in the listings API.

				:param onChangeFunctions: A list of callable objects to call when a change is noticed. (must each take a data object)
		'''
		return self._watchForNewIds(self.listing_api.getAllIds, onChangeFunctions)


	def watchForNewSecretListings(self, onChangeFunctions):
		'''
			Creates a watcher for if new item IDs appear in the listings API but not in the items API.

				:param onChangeFunctions: A list of callable objects to call when a change is noticed. (must each take a data object)
		'''
		def getSecretListingsWrapper()
			return getSecretListings(self.item_api, self.listing_api)

		return self._watchForNewIds(getSecretListingsWrapper, onChangeFunctions)


	#TODO: am I sure I don't want them to take this as a meta-watcher context?
	def halt(self):
		for watcher_thread in self.watcher_threads:
			watcher_thread.halt = True


	
if __name__ == "__main__":

	logger.setLevel(999)

	w = Watcher()

	def handler(signal, frame):
		print('halting.')
		w.halt()
		sys.exit()

	signal.signal(signal.SIGINT, handler)

	#t = WatcherTrigger(item_ids=[555], run_interval=30)
	#w.batchWatchListings([([t], [print])])

	def p_l(data):
		print("LISTINGS:")
		print(data)

	def p_i(data):
		print("Items:")
		print(data)

	def p_s(data):
		print("Secrets:")
		print(data)

	w.watchForNewItems([p_i])
	w.watchForNewListings([p_l])
	w.watchForNewSecretListings([p_s])

	if "alert" in sys.argv:
		def foundItemsCallback(new_items):
			found_string = "\nFOUND ITEMS:\n"
			for item in new_items:
				found_string += str(item)
			print(found_string)
			with open("new_items.log", 'a') as f:
				f.write(found_string)
				
		w.watchForNewItems([foundItemsCallback])
	else:
		while 1:
			pass
