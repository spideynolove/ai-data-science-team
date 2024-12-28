import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from typing import List, Dict, Any
import logging
from pymongo import MongoClient
from config import settings

class AnomalyDetector:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.mongo_client = MongoClient(settings.MONGODB_URI)
        self.models = {}

    async def detect_anomalies(self, collection_name: str, features: List[str]) -> Dict[str, Any]:
        """Detect anomalies in a collection using Isolation Forest"""
        try:
            # Get data from MongoDB
            db = self.mongo_client.get_database()
            collection = db[collection_name]
            data = list(collection.find({}))
            
            if not data:
                self.logger.warning(f"No data found in collection {collection_name}")
                return {"anomalies": [], "scores": []}
            
            # Convert to DataFrame
            df = pd.DataFrame(data)
            
            # Train or load model
            if collection_name not in self.models:
                self.models[collection_name] = IsolationForest(
                    contamination=0.05,
                    random_state=42
                )
                self.models[collection_name].fit(df[features])
            
            # Predict anomalies
            scores = self.models[collection_name].decision_function(df[features])
            predictions = self.models[collection_name].predict(df[features])
            
            # Get anomaly indices
            anomaly_indices = np.where(predictions == -1)[0]
            anomalies = df.iloc[anomaly_indices].to_dict('records')
            
            return {
                "anomalies": anomalies,
                "scores": scores.tolist()
            }
            
        except Exception as e:
            self.logger.error(f"Anomaly detection failed: {str(e)}")
            return {"anomalies": [], "scores": []}

    async def update_model(self, collection_name: str, features: List[str]) -> bool:
        """Update the anomaly detection model for a collection"""
        try:
            db = self.mongo_client.get_database()
            collection = db[collection_name]
            data = list(collection.find({}))
            
            if not data:
                self.logger.warning(f"No data found in collection {collection_name}")
                return False
                
            # Convert to DataFrame
            df = pd.DataFrame(data)
            
            # Train new model
            self.models[collection_name] = IsolationForest(
                contamination=0.05,
                random_state=42
            )
            self.models[collection_name].fit(df[features])
            
            return True
            
        except Exception as e:
            self.logger.error(f"Model update failed: {str(e)}")
            return False
