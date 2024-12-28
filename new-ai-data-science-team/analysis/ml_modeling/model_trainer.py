import pandas as pd
import numpy as np
from typing import Dict, Any
import logging
from pymongo import MongoClient
from config import settings
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import classification_report
import mlflow
import mlflow.sklearn
import optuna
from optuna.samplers import TPESampler

class ModelTrainer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.mongo_client = MongoClient(settings.MONGODB_URI)
        self.postgres_client = MongoClient(settings.POSTGRES_URI)
        mlflow.set_tracking_uri(settings.EXPERIMENT_TRACKING_URI)

    async def hyperparameter_tuning(self, model, param_grid: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform hyperparameter tuning using GridSearchCV"""
        try:
            grid_search = GridSearchCV(
                estimator=model,
                param_grid=param_grid,
                cv=5,
                scoring='accuracy',
                n_jobs=-1
            )
            grid_search.fit(data["X_train"], data["y_train"])
            
            return {
                "best_params": grid_search.best_params_,
                "best_score": grid_search.best_score_,
                "best_model": grid_search.best_estimator_
            }
        except Exception as e:
            self.logger.error(f"Hyperparameter tuning failed: {str(e)}")
            return {}

    async def objective(self, trial, model_class, data: Dict[str, Any]) -> float:
        """Objective function for Optuna optimization"""
        try:
            # Define hyperparameter space
            params = {
                'n_estimators': trial.suggest_int('n_estimators', 100, 1000),
                'max_depth': trial.suggest_int('max_depth', 3, 10),
                'min_samples_split': trial.suggest_int('min_samples_split', 2, 10),
                'min_samples_leaf': trial.suggest_int('min_samples_leaf', 1, 4)
            }
            
            # Initialize and train model
            model = model_class(**params)
            model.fit(data["X_train"], data["y_train"])
            
            # Evaluate model
            y_pred = model.predict(data["X_test"])
            return accuracy_score(data["y_test"], y_pred)
        except Exception as e:
            self.logger.error(f"Optimization trial failed: {str(e)}")
            return 0.0

    async def optimize_hyperparameters(self, model_class, data: Dict[str, Any], n_trials: int = 100) -> Dict[str, Any]:
        """Optimize hyperparameters using Optuna"""
        try:
            study = optuna.create_study(direction='maximize', sampler=TPESampler())
            study.optimize(lambda trial: self.objective(trial, model_class, data), n_trials=n_trials)
            
            return {
                "best_params": study.best_params,
                "best_value": study.best_value,
                "best_trial": study.best_trial
            }
        except Exception as e:
            self.logger.error(f"Hyperparameter optimization failed: {str(e)}")
            return {}

    async def evaluate_model(self, model, data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate model performance"""
        try:
            y_pred = model.predict(data["X_test"])
            report = classification_report(data["y_test"], y_pred, output_dict=True)
            
            return {
                "accuracy": report["accuracy"],
                "precision": report["weighted avg"]["precision"],
                "recall": report["weighted avg"]["recall"],
                "f1": report["weighted avg"]["f1-score"]
            }
        except Exception as e:
            self.logger.error(f"Model evaluation failed: {str(e)}")
            return {}

    async def train_with_optimization(self, model_class, data: Dict[str, Any], n_trials: int = 100) -> Dict[str, Any]:
        """Train model with hyperparameter optimization"""
        try:
            # Optimize hyperparameters
            optimization_result = await self.optimize_hyperparameters(model_class, data, n_trials)
            
            # Train final model with best parameters
            best_model = model_class(**optimization_result["best_params"])
            best_model.fit(data["X_train"], data["y_train"])
            
            # Evaluate final model
            evaluation_result = await self.evaluate_model(best_model, data)
            
            return {
                "model": best_model,
                "optimization_result": optimization_result,
                "evaluation_result": evaluation_result
            }
        except Exception as e:
            self.logger.error(f"Training with optimization failed: {str(e)}")
            return {}
