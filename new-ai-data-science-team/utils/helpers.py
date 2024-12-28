import logging
import json
from typing import Any, Dict, List
from datetime import datetime

class Helpers:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def json_serializer(self, obj: Any) -> str:
        """Serialize Python objects to JSON with datetime support"""
        try:
            if isinstance(obj, datetime):
                return obj.isoformat()
            return json.dumps(obj, default=str)
        except Exception as e:
            self.logger.error(f"JSON serialization failed: {str(e)}")
            return ""

    async def json_deserializer(self, json_str: str) -> Dict[str, Any]:
        """Deserialize JSON string to Python dictionary"""
        try:
            return json.loads(json_str)
        except Exception as e:
            self.logger.error(f"JSON deserialization failed: {str(e)}")
            return {}

    async def validate_schema(self, data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
        """Validate data against a JSON schema"""
        try:
            from jsonschema import validate
            validate(instance=data, schema=schema)
            return True
        except Exception as e:
            self.logger.error(f"Schema validation failed: {str(e)}")
            return False

    async def chunk_list(self, lst: List[Any], chunk_size: int) -> List[List[Any]]:
        """Split a list into chunks of specified size"""
        try:
            return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]
        except Exception as e:
            self.logger.error(f"List chunking failed: {str(e)}")
            return []

    async def flatten_list(self, nested_list: List[List[Any]]) -> List[Any]:
        """Flatten a nested list"""
        try:
            return [item for sublist in nested_list for item in sublist]
        except Exception as e:
            self.logger.error(f"List flattening failed: {str(e)}")
            return []

    async def safe_cast(self, value: Any, to_type: type, default: Any = None) -> Any:
        """Safely cast a value to a specified type"""
        try:
            return to_type(value)
        except (ValueError, TypeError):
            return default
