import pandas as pd
import numpy as np
from typing import Dict, Any
import logging
from pymongo import MongoClient
from config import settings
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import mlflow
import mlflow.sklearn

class ModelingAgent:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.mongo_client = MongoClient(settings.MONGODB_URI)
        self.postgres_client = MongoClient(settings.POSTGRES_URI)
        mlflow.set_tracking_uri(settings.EXPERIMENT_TRACKING_URI)

    async def prepare_data(self, df: pd.DataFrame, target_column: str) -> Dict[str, Any]:
        """Prepare data for modeling"""
        try:
            X = df.drop(columns=[target_column])
            y = df[target_column]
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            return {
                "X_train": X_train,
                "X_test": X_test,
                "y_train": y_train,
                "y_test": y_test
            }
        except Exception as e:
            self.logger.error(f"Data preparation failed: {str(e)}")
            return {}

    async def train_model(self, model_config: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Train a machine learning model"""
        try:
            model_type = model_config.get("type", "random_forest")
            
            with mlflow.start_run():
                # Log parameters
                mlflow.log_params(model_config.get("params", {}))
                
                # Initialize model
                if model_type == "random_forest":
                    model = RandomForestClassifier(**model_config.get("params", {}))
                elif model_type == "gradient_boosting":
                    model = GradientBoostingClassifier(**model_config.get("params", {}))
                elif model_type == "logistic_regression":
                    model = LogisticRegression(**model_config.get("params", {}))
                else:
                    raise ValueError(f"Unknown model type: {model_type}")
                
                # Train model
                model.fit(data["X_train"], data["y_train"])
                
                # Evaluate model
                y_pred = model.predict(data["X_test"])
                metrics = {
                    "accuracy": accuracy_score(data["y_test"], y_pred),
                    "precision": precision_score(data["y_test"], y_pred, average="weighted"),
                    "recall": recall_score(data["y_test"], y_pred, average="weighted"),
                    "f1": f1_score(data["y_test"], y_pred, average="weighted")
                }
                
                # Log metrics and model
                mlflow.log_metrics(metrics)
                mlflow.sklearn.log_model(model, "model")
                
                return {
                    "model": model,
                    "metrics": metrics,
                    "run_id": mlflow.active_run().info.run_id
                }
            
        except Exception as e:
            self.logger.error(f"Model training failed: {str(e)}")
            return {}

    async def register_model(self, run_id: str, model_name: str) -> bool:
        """Register model in MLflow Model Registry"""
        try:
            model_uri = f"runs:/{run_id}/model"
            mlflow.register_model(model_uri, model_name)
            return True
        except Exception as e:
            self.logger.error(f"Model registration failed: {str(e)}")
            return False

    async def predict(self, model, data: pd.DataFrame) -> np.ndarray:
        """Make predictions using trained model"""
        try:
            return model.predict(data)
        except Exception as e:
            self.logger.error(f"Prediction failed: {str(e)}")
            return np.array([])
