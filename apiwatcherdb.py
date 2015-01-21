import sqlite3

class Database:
	'''
		A database object for storing information on watcher subscriptions.
		Currently backed by sqlite.
	'''
	def __init__(self, db_file="./watchers.db"):
		'''
			Initialize a new database, or connect to an existing one.

				:param db_file: Path to the file to use as a db.  If it does not exist, it will be created.
		'''
		self.db_file = db_file

		self._createTables()

		connection = sqlite3.connect(self.db_file)
		cursor = connection.cursor()


	def _createTables(self):
		'''
			NOTE: inner function.
			Attempt to create the watchers, new_item_watchers, 
			new_listing_watchers, and new_secret_listing_watchers tables.
			Continues on OperationalError (already exists.)
		'''
		connection = sqlite3.connect(self.db_file)
		cursor = connection.cursor()

		try:
			cursor.execute("CREATE TABLE watchers (email text, id_list text, threshold char(50), value INT)")
		except sqlite3.OperationalError as e:
			pass
		try:
			cursor.execute("CREATE TABLE new_item_watchers (email text UNIQUE)")
		except sqlite3.OperationalError as e:
			pass
		try:
			cursor.execute("CREATE TABLE new_listing_watchers (email text UNIQUE)")
		except sqlite3.OperationalError as e:
			pass
		try:
			cursor.execute("CREATE TABLE new_secret_listing_watchers (email text UNIQUE)")
		except sqlite3.OperationalError as e:
			pass

		connection.commit()
		connection.close()


	def _addWatcherByTable(self, table, email, id_list=None, threshold=None, value=None):
		'''
			NOTE: inner function.
			Add a row to an arbitrary table.  Must contain at least an email field.
			If the watchers table is specified, the other arguments will be utilized.

				:param table: The table to insert into.
				:param email: The email to insert.
				:param id_list: (Only with watchers table) The listing ID list to watch
				:param threshold: (Only with watchers table) The threshold type
				:param value: (Only with watchers table) The value of the threshold
		'''
		try:
			connection = sqlite3.connect(self.db_file)
			cursor = connection.cursor()

			if table == "watchers":
				cursor.execute("INSERT INTO " + table + " VALUES (?, ?, ?, ?)", (email,id_list,threshold,value))
			else:
				cursor.execute("INSERT INTO " + table + " VALUES (?)", (email,))

			connection.commit()
			connection.close()
		except sqlite3.IntegrityError as e:
			return False
		return True


	def _getWatchersByTable(self, table, email=None):
		'''
			NOTE: inner function.
			Get all listings from an arbitrary table, with an optional where clause on email.

				:param table: The table to query.
				:param email: The email to select on.
		'''
		connection = sqlite3.connect(self.db_file)
		cursor = connection.cursor()

		if email:
			cursor.execute("SELECT * FROM " + table + " WHERE email = ?", (email,))
		else:
			cursor.execute("SELECT * FROM " + table)
		results = cursor.fetchall()

		connection.commit()
		connection.close()

		return results
		

	def getItemWatchers(self):
		'''
			Get all emails watching for new items.
		'''
		return self._getWatchersByTable("new_item_watchers")


	def getListingWatchers(self):
		'''
			Get all emails watching for new listings.
		'''
		return self._getWatchersByTable("new_listing_watchers")


	def getSecretListingWatchers(self):
		'''
			Get all emails watching for new secret listings.
		'''
		return self._getWatchersByTable("new_secret_listing_watchers")


	def getWatchers(self, email=None):
		'''
			Get all email/threhold listings.

				:param email: Only get thresholds for this email.
		'''
		return self._getWatchersByTable("watchers", email)


	def addItemWatcher(self, email):
		'''
			Add an email to those watching for new items.

				:param email: The new email to add.
		'''
		return self._addWatcherByTable("new_item_watchers", email)


	def addListingWatcher(self, email):
		'''
			Add an email to those watching for new listings.

				:param email: The new email to add.
		'''
		return self._addWatcherByTable("new_listing_watchers", email)


	def addSecretListingWatcher(self, email):
		'''
			Add an email to those watching for new secret listings.

				:param email: The new email to add.
		'''
		return self._addWatcherByTable("new_secret_listing_watchers", email)


	def addWatcher(self, email, id_list, threshold, value):
		'''
			Add an email to watch on arbitrary threshold data.

				:param email: The new email to add.
				:param id_list: The listing IDs to watch.
				:param threshold: The type of threshold to use.
				:param value: The threshold value.
		'''
		return self._addWatcherByTable("watchers", email, id_list, threshold, value)


