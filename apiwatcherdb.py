import sqlite3
import string
import random

class Timings:
	'''
		The various timing levels a watcher can trigger on.
	'''
	immediately = 0
	hourly = 1
	daily = 2


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
			cursor.execute("CREATE TABLE watchers (account text, id_list text, threshold char(50), value INT)")
		except sqlite3.OperationalError as e:
			pass
		try:
			cursor.execute("CREATE TABLE new_item_watchers (account text UNIQUE, timing INT)")
		except sqlite3.OperationalError as e:
			pass
		try:
			cursor.execute("CREATE TABLE new_listing_watchers (account text UNIQUE, timing INT)")
		except sqlite3.OperationalError as e:
			pass
		try:
			cursor.execute("CREATE TABLE new_secret_listing_watchers (account text UNIQUE, timing INT)")
		except sqlite3.OperationalError as e:
			pass

		try:
			cursor.execute("CREATE TABLE accounts (account text UNIQUE, hash char(128), salt char(32), unsubscription_token char(32))")
		except sqlite3.OperationalError as e:
			pass

		connection.commit()
		connection.close()


	def addAccount(self, account, password_hash, password_salt):
		'''
			Add a new account with credentials to the accounts table.

				:param account: The name of the account to add, must be unique.
				:param password_hash: The hash of the password to store.
				:param password_salt: The salt used to hash the password.
		'''
		try:
			connection = sqlite3.connect(self.db_file)
			cursor = connection.cursor()

			unsubscription_token = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for i in range(32))
			cursor.execute("INSERT INTO accounts VALUES (?, ?, ?, ?)", (account, password_hash, password_salt, unsubscription_token))

			connection.commit()
			connection.close()
		except sqlite3.IntegrityError as e:
			return False
		return True


	def getUnsubscriptionTokens(self, account):
		'''
			Get the unsubscription token for the account.

				:param account: Which account to get the token for.
		'''
		connection = sqlite3.connect(self.db_file)
		cursor = connection.cursor()

		cursor.execute("SELECT unsubscription_token FROM accounts WHERE account = ?", (account,))
		results = cursor.fetchone()

		connection.commit()
		connection.close()

		return results


	def getAccountTokens(self, account):
		'''
			Get the various security tokens associated with the account. (hash, salt)

				:param account: The account to get the tokens for.
		'''
		connection = sqlite3.connect(self.db_file)
		cursor = connection.cursor()

		cursor.execute("SELECT hash, salt FROM accounts WHERE account = ?", (account,))
		results = cursor.fetchone()

		connection.commit()
		connection.close()

		return results


	def _getAccounts(self):
		connection = sqlite3.connect(self.db_file)
		cursor = connection.cursor()

		cursor.execute("SELECT * FROM accounts ")
		results = cursor.fetchall()

		connection.commit()
		connection.close()

		return results


	def removeAccount(self, account, unsubscription_token):
		'''
			Remove an account from the account store.  Requires a valid unsubscription token.

				:param account: The account to remove.
				:param unsubscription_token: The unsubscription token stored with the account.
		'''
		try:
			connection = sqlite3.connect(self.db_file)
			cursor = connection.cursor()

			cursor.execute("DELETE FROM accounts WHERE account = ? AND unsubscription = ?", (account, unsubscription_token))

			self.removeItemWatcher(account)
			self.removeListingWatcher(account)
			self.removeSecretListingWatcher(account)
			self.removeWatcher(account)

			connection.commit()
			connection.close()
		except Exception as e:
			print(e)
			return False
		return True
	

	def _removeWatcherByTable(self, table, account, id_list=None, threshold=None, value=None):
		'''
			NOTE: inner function.
			Remove a row from an arbitrary table.  Must contain at least an account field.
			If the watchers table is specified, the other arguments will be utilized.

				:param table: The table to remove into.
				:param account: The account to remove.
				:param id_list: (Only with watchers table) the id list to match
				:param threshold: (Only with watchers table) the threshold to match
				:param value: (Only with watchers table) the value to match.
		'''
		try:
			connection = sqlite3.connect(self.db_file)
			cursor = connection.cursor()

			if table == "watchers" and id_list != None and threshold != None and value != None:
				cursor.execute("DELETE FROM " + table + " WHERE account = ? AND threshold = ? AND value = ?", (account, threshold, value))
			else:
				cursor.execute("DELETE FROM " + table + " WHERE account = ?", (account,))

			connection.commit()
			connection.close()
		except Exception as e:
			print(e)
			return False
		return True


	def _addWatcherByTable(self, table, account, id_list=None, threshold=None, value=None, timing=Timings.immediate):
		'''
			NOTE: inner function.
			Add a row to an arbitrary table.  Must contain at least an account field.
			If the watchers table is specified, the other arguments will be utilized.

				:param table: The table to insert into.
				:param account: The account to insert.
				:param id_list: (Only with watchers table) The listing ID list to watch
				:param threshold: (Only with watchers table) The threshold type
				:param value: (Only with watchers table) The value of the threshold
		'''
		try:
			connection = sqlite3.connect(self.db_file)
			cursor = connection.cursor()

			if table == "watchers":
				cursor.execute("INSERT INTO " + table + " VALUES (?, ?, ?, ?)", (account,id_list,threshold,value))
			else:
				cursor.execute("INSERT INTO " + table + " VALUES (?, ?)", (account,timing))

			connection.commit()
			connection.close()
		except sqlite3.IntegrityError as e:
			return False
		return True


	def _getWatchersByTable(self, table, account=None):
		'''
			NOTE: inner function.
			Get all listings from an arbitrary table, with an optional where clause on account.

				:param table: The table to query.
				:param account: The account to select on.
		'''
		connection = sqlite3.connect(self.db_file)
		cursor = connection.cursor()

		if account:
			cursor.execute("SELECT * FROM " + table + " WHERE account = ?", (account,))
		else:
			cursor.execute("SELECT * FROM " + table)
		results = cursor.fetchall()

		connection.commit()
		connection.close()

		return results
		

	def getItemWatchers(self, account=None):
		'''
			Get all accounts watching for new items.

				:param account: Only for the specified account.
		'''
		return self._getWatchersByTable("new_item_watchers", account)


	def getListingWatchers(self, account=None):
		'''
			Get all accounts watching for new listings.

				:param account: Only for the specified account.
		'''
		return self._getWatchersByTable("new_listing_watchers", account)


	def getSecretListingWatchers(self, account=None):
		'''
			Get all accounts watching for new secret listings.

				:param account: Only for the specified account.
		'''
		return self._getWatchersByTable("new_secret_listing_watchers", account)


	def getWatchers(self, account=None):
		'''
			Get all account/threhold listings.

				:param account: Only get thresholds for this account.
		'''
		return self._getWatchersByTable("watchers", account)


	def addItemWatcher(self, account, timing=Timings.daily):
		'''
			Add an account to those watching for new items.

				:param account: The new account to add.
		'''
		return self._addWatcherByTable("new_item_watchers", account, timing=timing)


	def addListingWatcher(self, account, timing=Timings.daily):
		'''
			Add an account to those watching for new listings.

				:param account: The new account to add.
		'''
		return self._addWatcherByTable("new_listing_watchers", account, timing=timing)


	def addSecretListingWatcher(self, account, timing=Timings.daily):
		'''
			Add an account to those watching for new secret listings.

				:param account: The new account to add.
		'''
		return self._addWatcherByTable("new_secret_listing_watchers", account, timing=timing)


	def addWatcher(self, account, id_list, threshold, value):
		'''
			Add an account to watch on arbitrary threshold data.

				:param account: The new account to add.
				:param id_list: The listing IDs to watch.
				:param threshold: The type of threshold to use.
				:param value: The threshold value.
		'''
		return self._addWatcherByTable("watchers", account, id_list, threshold, value)


	def removeItemWatcher(self, account):
		'''
			Remove an account to those watching for new items.

				:param account: The new account to remove.
		'''
		return self._removeWatcherByTable("new_item_watchers", account)


	def removeListingWatcher(self, account):
		'''
			Remove an account to those watching for new listings.

				:param account: The new account to remove.
		'''
		return self._removeWatcherByTable("new_listing_watchers", account)


	def removeSecretListingWatcher(self, account):
		'''
			Remove an account to those watching for new secret listings.

				:param account: The new account to remove.
		'''
		return self._removeWatcherByTable("new_secret_listing_watchers", account)


	def removeWatcher(self, account, id_list=None, threshold=None, value=None):
		'''
			Remove an account to watch on arbitrary threshold data.

				:param account: The new account to remove.

			NOTE: if the following are not populated, all watchers with the account will be removed.

				:param id_list: The listing IDs to match.
				:param threshold: The type of threshold to match.
				:param value: The threshold value to match.
		'''
		return self._removeWatcherByTable("watchers", account, id_list, threshold, value)


