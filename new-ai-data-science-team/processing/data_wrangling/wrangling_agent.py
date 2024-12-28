import pandas as pd
import numpy as np
from typing import List, Dict, Any
import logging
from pymongo import MongoClient
from config import settings

class WranglingAgent:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.mongo_client = MongoClient(settings.MONGODB_URI)
        self.postgres_client = MongoClient(settings.POSTGRES_URI)

    async def merge_data_sources(self, collection_names: List[str], merge_keys: Dict[str, str]) -> pd.DataFrame:
        """Merge data from multiple MongoDB collections"""
        try:
            db = self.mongo_client.get_database()
            dfs = []
            
            for collection_name in collection_names:
                collection = db[collection_name]
                data = list(collection.find({}))
                if data:
                    df = pd.DataFrame(data)
                    dfs.append(df)
            
            if not dfs:
                self.logger.warning("No data found in specified collections")
                return pd.DataFrame()
            
            # Merge dataframes
            merged_df = dfs[0]
            for df in dfs[1:]:
                merged_df = pd.merge(
                    merged_df,
                    df,
                    how='outer',
                    left_on=merge_keys.get('left'),
                    right_on=merge_keys.get('right')
                )
            
            return merged_df
            
        except Exception as e:
            self.logger.error(f"Data merging failed: {str(e)}")
            return pd.DataFrame()

    async def standardize_formats(self, df: pd.DataFrame, format_spec: Dict[str, Any]) -> pd.DataFrame:
        """Standardize data formats according to specification"""
        try:
            # Convert data types
            for col, dtype in format_spec.get('dtypes', {}).items():
                if col in df.columns:
                    df[col] = df[col].astype(dtype)
            
            # Standardize date formats
            for col in format_spec.get('date_columns', []):
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
            
            # Standardize categorical values
            for col, categories in format_spec.get('categories', {}).items():
                if col in df.columns:
                    df[col] = pd.Categorical(df[col], categories=categories)
            
            # Handle missing values
            for col, fill_value in format_spec.get('missing_values', {}).items():
                if col in df.columns:
                    df[col].fillna(fill_value, inplace=True)
            
            return df
            
        except Exception as e:
            self.logger.error(f"Format standardization failed: {str(e)}")
            return df

    async def store_processed_data(self, df: pd.DataFrame, table_name: str) -> bool:
        """Store processed data in PostgreSQL"""
        try:
            if df.empty:
                self.logger.warning("Empty dataframe, nothing to store")
                return False
                
            # Convert dataframe to records
            records = df.to_dict('records')
            
            # Store in PostgreSQL
            db = self.postgres_client.get_database()
            collection = db[table_name]
            collection.insert_many(records)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to store processed data: {str(e)}")
            return False
