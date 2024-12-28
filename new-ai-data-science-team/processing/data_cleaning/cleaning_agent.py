import pandas as pd
import numpy as np
from typing import Dict, Any
import logging
from pymongo import MongoClient
from config import settings
from pandas_profiling import ProfileReport
from dedupe import Dedupe

class CleaningAgent:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.mongo_client = MongoClient(settings.MONGODB_URI)
        self.postgres_client = MongoClient(settings.POSTGRES_URI)

    async def analyze_data_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze data quality using Pandas Profiling"""
        try:
            profile = ProfileReport(df, minimal=True)
            quality_report = profile.get_description()
            
            return {
                "missing_values": quality_report["table"]["n_missing"],
                "duplicates": quality_report["table"]["n_duplicates"],
                "variables": {
                    var: {
                        "type": stats["type"],
                        "missing": stats["n_missing"],
                        "unique": stats["n_unique"]
                    }
                    for var, stats in quality_report["variables"].items()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Data quality analysis failed: {str(e)}")
            return {}

    async def handle_missing_values(self, df: pd.DataFrame, strategy: Dict[str, Any]) -> pd.DataFrame:
        """Handle missing values based on specified strategy"""
        try:
            for col, method in strategy.items():
                if col not in df.columns:
                    continue
                    
                if method == "drop":
                    df.dropna(subset=[col], inplace=True)
                elif method == "mean":
                    df[col].fillna(df[col].mean(), inplace=True)
                elif method == "median":
                    df[col].fillna(df[col].median(), inplace=True)
                elif method == "mode":
                    df[col].fillna(df[col].mode()[0], inplace=True)
                elif isinstance(method, (int, float, str)):
                    df[col].fillna(method, inplace=True)
            
            return df
            
        except Exception as e:
            self.logger.error(f"Missing value handling failed: {str(e)}")
            return df

    async def deduplicate_data(self, df: pd.DataFrame, fields: List[str]) -> pd.DataFrame:
        """Remove duplicate records using Dedupe"""
        try:
            if not fields:
                return df.drop_duplicates()
                
            # Initialize Dedupe
            deduper = Dedupe(fields)
            
            # Prepare data for deduplication
            records = df.to_dict('records')
            deduper.prepare_training(records)
            
            # Train and deduplicate
            deduper.train()
            clustered_dupes = deduper.match(records, threshold=0.5)
            
            # Remove duplicates
            unique_indices = set()
            for cluster in clustered_dupes:
                unique_indices.add(cluster[0])
                
            return df.iloc[list(unique_indices)]
            
        except Exception as e:
            self.logger.error(f"Deduplication failed: {str(e)}")
            return df.drop_duplicates()

    async def clean_data(self, df: pd.DataFrame, cleaning_config: Dict[str, Any]) -> pd.DataFrame:
        """Perform comprehensive data cleaning"""
        try:
            # Handle missing values
            if "missing_values" in cleaning_config:
                df = await self.handle_missing_values(df, cleaning_config["missing_values"])
            
            # Deduplicate data
            if "deduplication" in cleaning_config:
                df = await self.deduplicate_data(df, cleaning_config["deduplication"].get("fields", []))
            
            return df
            
        except Exception as e:
            self.logger.error(f"Data cleaning failed: {str(e)}")
            return df
