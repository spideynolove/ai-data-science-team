import pandas as pd
from typing import List, Dict, Any
import logging
from pymongo import MongoClient
from config import settings
from great_expectations import dataset

class DataMerger:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.mongo_client = MongoClient(settings.MONGODB_URI)
        self.postgres_client = MongoClient(settings.POSTGRES_URI)

    async def validate_merge(self, df: pd.DataFrame, validation_rules: Dict[str, Any]) -> bool:
        """Validate merged data using Great Expectations"""
        try:
            # Create Great Expectations dataset
            ge_df = dataset.PandasDataset(df)
            
            # Apply validation rules
            for column, rules in validation_rules.items():
                if column not in df.columns:
                    continue
                    
                for rule_type, rule_params in rules.items():
                    if rule_type == "not_null":
                        ge_df.expect_column_values_to_not_be_null(column)
                    elif rule_type == "unique":
                        ge_df.expect_column_values_to_be_unique(column)
                    elif rule_type == "in_set":
                        ge_df.expect_column_values_to_be_in_set(column, rule_params)
                    elif rule_type == "between":
                        ge_df.expect_column_values_to_be_between(
                            column,
                            min_value=rule_params.get('min'),
                            max_value=rule_params.get('max')
                        )
            
            # Get validation results
            results = ge_df.validate()
            if not results["success"]:
                self.logger.error(f"Merge validation failed: {results['results']}")
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"Merge validation error: {str(e)}")
            return False

    async def merge_with_validation(self, sources: List[str], merge_config: Dict[str, Any]) -> pd.DataFrame:
        """Merge data sources with validation"""
        try:
            # Get data from MongoDB
            db = self.mongo_client.get_database()
            dfs = []
            
            for source in sources:
                collection = db[source]
                data = list(collection.find({}))
                if data:
                    df = pd.DataFrame(data)
                    dfs.append(df)
            
            if not dfs:
                self.logger.warning("No data found in specified sources")
                return pd.DataFrame()
            
            # Perform merge
            merged_df = dfs[0]
            for df in dfs[1:]:
                merged_df = pd.merge(
                    merged_df,
                    df,
                    how=merge_config.get('how', 'inner'),
                    left_on=merge_config.get('left_on'),
                    right_on=merge_config.get('right_on')
                )
            
            # Validate merged data
            if not await self.validate_merge(merged_df, merge_config.get('validation_rules', {})):
                self.logger.error("Merge validation failed")
                return pd.DataFrame()
            
            return merged_df
            
        except Exception as e:
            self.logger.error(f"Data merge failed: {str(e)}")
            return pd.DataFrame()
