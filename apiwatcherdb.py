import sqlite3

class Database:
	def __init__(self, db_file="./watchers.db"):
		self.db_file = db_file

		self.createTables()

		connection = sqlite3.connect(self.db_file)
		cursor = connection.cursor()


	def createTables(self):
		connection = sqlite3.connect(self.db_file)
		cursor = connection.cursor()

		try:
			#TODO: make the email get a unique constraint.
			cursor.execute("CREATE TABLE new_item_watchers (email text UNIQUE)")
			cursor.execute("CREATE TABLE new_listing_watchers (email text UNIQUE)")
			cursor.execute("CREATE TABLE new_secret_listing_watchers (email text UNIQUE)")
		except sqlite3.OperationalError as e:
			pass

		connection.commit()
		connection.close()


	def addWatcherByTable(self, table, email):
		try:
			connection = sqlite3.connect(self.db_file)
			cursor = connection.cursor()

			cursor.execute("INSERT INTO " + table + " VALUES (?)", (email,))

			connection.commit()
			connection.close()
		except sqlite3.IntegrityError as e:
			return False
		return True


	def getWatchersByTable(self, table):
		connection = sqlite3.connect(self.db_file)
		cursor = connection.cursor()

		cursor.execute("SELECT * FROM " + table)
		results = cursor.fetchall()

		connection.commit()
		connection.close()

		return results
		

	def getItemWatchers(self):
		return self.getWatchersByTable("new_item_watchers")


	def getListingWatchers(self):
		return self.getWatchersByTable("new_listing_watchers")


	def getSecretListingWatchers(self):
		return self.getWatchersByTable("new_secret_listing_watchers")


	def addItemWatcher(self, email):
		return self.addWatcherByTable("new_item_watchers", email)


	def addListingWatcher(self, email):
		return self.addWatcherByTable("new_listing_watchers", email)


	def addSecretListingWatcher(self, email):
		return self.addWatcherByTable("new_secret_listing_watchers", email)


