import pandas as pd
import numpy as np
from typing import List, Dict, Any
import logging
from pymongo import MongoClient
from config import settings
from feature_engine import creation, selection
from sklearn.feature_selection import mutual_info_classif

class EngineeringAgent:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.mongo_client = MongoClient(settings.MONGODB_URI)
        self.postgres_client = MongoClient(settings.POSTGRES_URI)

    async def create_features(self, df: pd.DataFrame, feature_config: Dict[str, Any]) -> pd.DataFrame:
        """Create new features based on configuration"""
        try:
            # Create mathematical features
            if "math_operations" in feature_config:
                for operation in feature_config["math_operations"]:
                    df[operation["new_feature"]] = eval(operation["expression"])
            
            # Create interaction features
            if "interactions" in feature_config:
                for interaction in feature_config["interactions"]:
                    df[interaction["new_feature"]] = df[interaction["features"]].prod(axis=1)
            
            # Create datetime features
            if "datetime_features" in feature_config:
                for dt_feature in feature_config["datetime_features"]:
                    if dt_feature["column"] in df.columns:
                        df[dt_feature["new_feature"]] = pd.to_datetime(df[dt_feature["column"]]).dt[dt_feature["attribute"]]
            
            return df
            
        except Exception as e:
            self.logger.error(f"Feature creation failed: {str(e)}")
            return df

    async def select_features(self, df: pd.DataFrame, target: str, selection_config: Dict[str, Any]) -> pd.DataFrame:
        """Select relevant features based on configuration"""
        try:
            # Remove constant features
            if selection_config.get("remove_constant", False):
                selector = selection.DropConstantFeatures(tol=1.0)
                df = selector.fit_transform(df)
            
            # Remove correlated features
            if selection_config.get("remove_correlated", False):
                selector = selection.SmartCorrelationSelection(
                    threshold=selection_config.get("correlation_threshold", 0.8)
                )
                df = selector.fit_transform(df)
            
            # Select features by importance
            if selection_config.get("feature_importance", False):
                X = df.drop(columns=[target])
                y = df[target]
                importance = mutual_info_classif(X, y)
                important_features = X.columns[importance > selection_config.get("importance_threshold", 0.0)]
                df = df[important_features.tolist() + [target]]
            
            return df
            
        except Exception as e:
            self.logger.error(f"Feature selection failed: {str(e)}")
            return df

    async def store_features(self, df: pd.DataFrame, feature_store_name: str) -> bool:
        """Store engineered features in feature store"""
        try:
            if df.empty:
                self.logger.warning("Empty dataframe, nothing to store")
                return False
                
            # Convert dataframe to records
            records = df.to_dict('records')
            
            # Store in feature store
            db = self.postgres_client.get_database()
            collection = db[feature_store_name]
            collection.insert_many(records)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to store features: {str(e)}")
            return False
