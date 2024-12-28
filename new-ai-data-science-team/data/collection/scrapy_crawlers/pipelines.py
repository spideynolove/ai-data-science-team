import logging
from itemadapter import ItemAdapter
from pymongo import MongoClient
from config import settings
from ..validation_agent import ValidationAgent
from ..schema_validator import SchemaValidator
from ..anomaly_detector import AnomalyDetector

class DataQualityPipeline:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.mongo_client = MongoClient(settings.MONGODB_URI)
        self.validation_agent = ValidationAgent()
        self.schema_validator = SchemaValidator()
        self.anomaly_detector = AnomalyDetector()

    async def process_item(self, item, spider):
        """Process each item through the data quality pipeline"""
        try:
            # Convert item to dict
            item_dict = ItemAdapter(item).asdict()
            
            # Validate data
            if not await self.validation_agent.validate_data(spider.name, item_dict):
                self.logger.error(f"Validation failed for item: {item_dict}")
                return None
                
            # Validate against schema
            if not await self.schema_validator.validate_against_schema(spider.name, item_dict):
                self.logger.error(f"Schema validation failed for item: {item_dict}")
                return None
                
            # Check for anomalies
            features = list(item_dict.keys())
            anomaly_result = await self.anomaly_detector.detect_anomalies(spider.name, features)
            if item_dict in anomaly_result["anomalies"]:
                self.logger.warning(f"Anomaly detected in item: {item_dict}")
                return None
                
            # Store valid item in MongoDB
            db = self.mongo_client.get_database()
            collection = db[spider.name]
            collection.insert_one(item_dict)
            
            return item
            
        except Exception as e:
            self.logger.error(f"Pipeline processing error: {str(e)}")
            return None

class MongoDBPipeline:
    def __init__(self):
        self.mongo_client = MongoClient(settings.MONGODB_URI)
        
    def close_spider(self, spider):
        self.mongo_client.close()

    async def process_item(self, item, spider):
        """Store item in MongoDB"""
        try:
            db = self.mongo_client.get_database()
            collection = db[spider.name]
            collection.insert_one(ItemAdapter(item).asdict())
            return item
        except Exception as e:
            spider.logger.error(f"Failed to store item in MongoDB: {str(e)}")
            return None
