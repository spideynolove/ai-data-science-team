import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
from config import settings

class MongoDBClient:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.client = MongoClient(settings.MONGODB_URI)
        self.db = self.client.get_database()

    async def insert_document(self, collection_name: str, document: dict) -> bool:
        """Insert a single document into MongoDB"""
        try:
            collection = self.db[collection_name]
            result = collection.insert_one(document)
            return result.acknowledged
        except (ConnectionFailure, OperationFailure) as e:
            self.logger.error(f"MongoDB operation failed: {str(e)}")
            return False

    async def find_document(self, collection_name: str, query: dict) -> dict:
        """Find a single document in MongoDB"""
        try:
            collection = self.db[collection_name]
            return collection.find_one(query)
        except (ConnectionFailure, OperationFailure) as e:
            self.logger.error(f"MongoDB operation failed: {str(e)}")
            return {}

    async def update_document(self, collection_name: str, query: dict, update: dict) -> bool:
        """Update a document in MongoDB"""
        try:
            collection = self.db[collection_name]
            result = collection.update_one(query, {'$set': update})
            return result.acknowledged
        except (ConnectionFailure, OperationFailure) as e:
            self.logger.error(f"MongoDB operation failed: {str(e)}")
            return False

    async def delete_document(self, collection_name: str, query: dict) -> bool:
        """Delete a document from MongoDB"""
        try:
            collection = self.db[collection_name]
            result = collection.delete_one(query)
            return result.acknowledged
        except (ConnectionFailure, OperationFailure) as e:
            self.logger.error(f"MongoDB operation failed: {str(e)}")
            return False

    async def close(self):
        """Close MongoDB connection"""
        try:
            self.client.close()
            return True
        except Exception as e:
            self.logger.error(f"Failed to close MongoDB connection: {str(e)}")
            return False
