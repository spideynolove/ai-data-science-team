import json
import jsonschema
from typing import Dict, Any
import logging
from pymongo import MongoClient
from config import settings

class SchemaValidator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.mongo_client = MongoClient(settings.MONGODB_URI)
        self.schema_cache = {}

    async def validate_against_schema(self, collection_name: str, document: Dict[str, Any]) -> bool:
        """Validate a document against its JSON schema"""
        try:
            # Get schema from MongoDB
            if collection_name not in self.schema_cache:
                db = self.mongo_client.get_database()
                schema_collection = db["schemas"]
                schema = schema_collection.find_one({"collection": collection_name})
                if not schema:
                    self.logger.error(f"No schema found for collection {collection_name}")
                    return False
                self.schema_cache[collection_name] = schema["schema"]
            
            # Validate document
            jsonschema.validate(
                instance=document,
                schema=self.schema_cache[collection_name]
            )
            return True
            
        except jsonschema.ValidationError as e:
            self.logger.error(f"Schema validation failed: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Validation error: {str(e)}")
            return False

    async def register_schema(self, collection_name: str, schema: Dict[str, Any]) -> bool:
        """Register a new JSON schema for a collection"""
        try:
            db = self.mongo_client.get_database()
            schema_collection = db["schemas"]
            
            # Update or insert schema
            result = schema_collection.update_one(
                {"collection": collection_name},
                {"$set": {"schema": schema}},
                upsert=True
            )
            
            # Update cache
            self.schema_cache[collection_name] = schema
            
            return result.acknowledged
            
        except Exception as e:
            self.logger.error(f"Failed to register schema: {str(e)}")
            return False
