import great_expectations as ge
from pymongo import MongoClient
from typing import Dict, Any
import logging
from config import settings

class ValidationAgent:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.mongo_client = MongoClient(settings.MONGODB_URI)
        self.context = ge.get_context()
        
        # Configure Great Expectations
        self.datasource_config = {
            "name": "mongo_datasource",
            "class_name": "Datasource",
            "module_name": "great_expectations.datasource",
            "execution_engine": {
                "module_name": "great_expectations.execution_engine",
                "class_name": "PandasExecutionEngine",
            },
            "data_connectors": {
                "default_runtime_data_connector": {
                    "class_name": "RuntimeDataConnector",
                    "batch_identifiers": ["default_identifier_name"],
                }
            },
        }
        self.context.add_datasource(**self.datasource_config)

    async def validate_data(self, collection_name: str, schema: Dict[str, Any]) -> bool:
        """Validate data against schema using Great Expectations"""
        try:
            # Get data from MongoDB
            db = self.mongo_client.get_database()
            collection = db[collection_name]
            data = list(collection.find({}))
            
            # Create expectation suite
            suite = self.context.create_expectation_suite(
                expectation_suite_name=f"{collection_name}_validation"
            )
            
            # Add schema-based expectations
            for field, field_spec in schema.items():
                suite.add_expectation(
                    ge.core.ExpectationConfiguration(
                        expectation_type="expect_column_to_exist",
                        kwargs={"column": field}
                    )
                )
                
                if field_spec.get("type"):
                    suite.add_expectation(
                        ge.core.ExpectationConfiguration(
                            expectation_type="expect_column_values_to_be_of_type",
                            kwargs={
                                "column": field,
                                "type_": field_spec["type"]
                            }
                        )
                    )
                
                if field_spec.get("required"):
                    suite.add_expectation(
                        ge.core.ExpectationConfiguration(
                            expectation_type="expect_column_values_to_not_be_null",
                            kwargs={"column": field}
                        )
                    )
            
            # Validate data
            results = self.context.run_validation_operator(
                "action_list_operator",
                assets_to_validate=[{
                    "batch_kwargs": {
                        "dataset": data,
                        "datasource": "mongo_datasource"
                    },
                    "expectation_suite_name": suite.expectation_suite_name
                }]
            )
            
            if not results["success"]:
                self.logger.error(f"Validation failed for {collection_name}")
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"Validation error: {str(e)}")
            return False
