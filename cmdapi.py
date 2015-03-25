import listings
import items
import copy
import util


class Query:
	'''
		Query object, presents the ability to chain additional filters or produce an evaluation of the result space,
		merging the various api channels for the relevent artifact type.
	'''
	results = []
	fields = []
	tables = {}


	def __init__(self, parent, results=None):
		'''
			Initialize a new query.  Takes either a set of tables (as {table_name:[objects]} ) for the
			initial declaration of a query stanza, or a parent query and a set of results to inherit
			if further down the chain.

				:param parent: Either the tables to start a query stanza against, or the parent query.
				:param results: If a parent query is specified, these are the results to inherit.
		'''
		#Initial setup from the api wrapper.
		if results == None:
			self.tables = parent
			return

		self.fields = parent.fields
		self.tables = parent.tables
		self.results = results


	def Select(self, *fields):
		'''
			Specify which fields to include in the returned rows when evaluating the query.

				:param fields: The names of the fields to return in a list of tuples.
		'''
		query = Query(self, self.results)
		query.fields = fields
		return query


	def From(self, artifact_type):
		'''
			Declare the type you want to query (to keep our options open for doing recipes and stuff later.)

				:param artifact_type: The type to query.  Must be from within the table dict passed in during
					initial query stanza initialization.
		'''
		results = [{artifact_type:artifact} for artifact in self.tables[artifact_type]]
		return Query(self, results)


	#Not a huge fan of how I do join, but "it works" I guess.
	def Join(self, artifact_type, field, original_field=None):
		'''
			Perform a join with another type specified in the tables dict.  Utilize shared field.  If field isn't shared,
			specify the original field in the final arg.

				:param artifact_type: Which new table to join.
				:param field: Name of the field to join the new table to results with.
				:param original_field: Name of the field that should already be contained within the results to join
					the new tables field with.
		'''
		if original_field == None:
			original_field = field

		joinable_index = {}
		for artifact_group in self.results:
			for artifact in artifact_group.values():
				try:
					joinable_index[getattr(artifact, original_field)] = copy.deepcopy(artifact_group)
				except AttributeError:
					pass
 
		for artifact in self.tables[artifact_type]:
			try:
				joinable_index[getattr(artifact, field)][artifact_type] = artifact
			except KeyError:
				pass
			except AttributeError:
				pass

		return Query(self, list(joinable_index.values()))
		


	def Where(self, query):
		'''
			Add a where clause to the query.  Returns a new query object that has been filtered accordingly.

				:param query: The lambda to examine each object for validity.
		'''
		results = []
		for artifact_group in self.results:
			if query(artifact_group):
				results.append(artifact_group)
		
		return Query(self, results)


	#TODO: don't like how I do missing columns right now, they just get left out from the results.
	def Evaluate(self):
		'''
			Get the fields specified via select for each joined object, and return a list of tuples.
		'''

		selected_results = []
		for artifact_group in self.results:
			result_batch = {}
			for field in self.fields:
				for artifact in artifact_group.values():
					try:
						result_batch[field] = getattr(artifact, field)
						break
					except AttributeError:
						result_batch[field] = None
						pass

			if result_batch:
				selected_results.append(result_batch)

		return selected_results

class Api:
	'''
		Command line API library.  Mostly used in the absence of a good DB backend; implements
		primarily sql like where filtering with lambdas.
		Thus far only supports item/listing queries. (because that's what I needed.)
	'''

	data = {}

	def __init__(self):
		'''
			Prime the API with current data.  This takes a bit.
		'''
		listing_api = listings.Listings()
		self.data['listings'] = listing_api.getAllListings()

		item_api = items.Items()
		self.data['items'] = item_api.getAllItems()


	def Query(self):
		'''
			Begin a query stanza.  
		'''
		return Query(self.data)


