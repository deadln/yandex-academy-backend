import pymongo

class Database:
    def __init__(self):
        # Create the client
        self.client = pymongo.MongoClient('localhost', 27017)

        # Connect to our database
        self.db = self.client['SeriesDB']

        # Fetch our series collection
        #self.couriers_collection = self.db['couriers']

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(Database, cls).__new__(cls)
        return cls.instance

    def insert_document(self, collection_name, data):
        collection = self.db[collection_name]
        """ Function to insert a document into a collection and
        return the document's id.
        """
        return collection.insert_one(data).inserted_id

    def find_document(self, collection_name, elements, multiple=False):
        collection = self.db[collection_name]
        """ Function to retrieve single or multiple documents from a provided
        Collection using a dictionary containing a document's elements.
        """
        if multiple:
            results = collection.find(elements)
            return [r for r in results]
        else:
            return collection.find_one(elements)

    def update_document(self, collection_name, query_elements, new_values):
        collection = self.db[collection_name]
        """ Function to update a single document in a collection.
        """
        collection.update_one(query_elements, {'$set': new_values})

    def delete_document(self, collection_name, query):
        collection = self.db[collection_name]
        """ Function to delete a single document from a collection.
        """
        collection.delete_one(query)