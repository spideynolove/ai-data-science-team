import pandas as pd
import numpy as np
from typing import Dict, Any
import logging
from pymongo import MongoClient
from config import settings
import shap
import lime
import lime.lime_tabular
from alibi.explainers import AnchorTabular
import mlflow

class InterpretabilityAgent:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.mongo_client = MongoClient(settings.MONGODB_URI)
        self.postgres_client = MongoClient(settings.POSTGRES_URI)
        mlflow.set_tracking_uri(settings.EXPERIMENT_TRACKING_URI)

    async def explain_with_shap(self, model, data: pd.DataFrame) -> Dict[str, Any]:
        """Explain model predictions using SHAP"""
        try:
            explainer = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(data)
            
            return {
                "shap_values": shap_values,
                "expected_value": explainer.expected_value,
                "feature_importance": np.abs(shap_values).mean(axis=0).tolist()
            }
        except Exception as e:
            self.logger.error(f"SHAP explanation failed: {str(e)}")
            return {}

    async def explain_with_lime(self, model, data: pd.DataFrame, feature_names: List[str]) -> Dict[str, Any]:
        """Explain model predictions using LIME"""
        try:
            explainer = lime.lime_tabular.LimeTabularExplainer(
                data.values,
                feature_names=feature_names,
                class_names=['0', '1'],
                verbose=True,
                mode='classification'
            )
            
            explanations = []
            for i in range(min(5, len(data))):
                exp = explainer.explain_instance(
                    data.iloc[i].values,
                    model.predict_proba,
                    num_features=5
                )
                explanations.append(exp.as_list())
            
            return {
                "explanations": explanations
            }
        except Exception as e:
            self.logger.error(f"LIME explanation failed: {str(e)}")
            return {}

    async def explain_with_anchors(self, model, data: pd.DataFrame, feature_names: List[str]) -> Dict[str, Any]:
        """Explain model predictions using Anchors"""
        try:
            explainer = AnchorTabular(
                model.predict,
                feature_names,
                categorical_names={}
            )
            explainer.fit(data.values)
            
            explanations = []
            for i in range(min(5, len(data))):
                explanation = explainer.explain(data.iloc[i].values)
                explanations.append({
                    "anchor": explanation.anchor,
                    "precision": explanation.precision,
                    "coverage": explanation.coverage
                })
            
            return {
                "explanations": explanations
            }
        except Exception as e:
            self.logger.error(f"Anchors explanation failed: {str(e)}")
            return {}

    async def generate_interpretability_report(self, model, data: pd.DataFrame, feature_names: List[str]) -> Dict[str, Any]:
        """Generate comprehensive interpretability report"""
        try:
            shap_results = await self.explain_with_shap(model, data)
            lime_results = await self.explain_with_lime(model, data, feature_names)
            anchors_results = await self.explain_with_anchors(model, data, feature_names)
            
            return {
                "shap": shap_results,
                "lime": lime_results,
                "anchors": anchors_results
            }
        except Exception as e:
            self.logger.error(f"Interpretability report generation failed: {str(e)}")
            return {}

    async def log_interpretability(self, run_id: str, interpretability_results: Dict[str, Any]) -> bool:
        """Log interpretability results in MLflow"""
        try:
            with mlflow.start_run(run_id=run_id):
                mlflow.log_dict(interpretability_results, "interpretability.json")
            return True
        except Exception as e:
            self.logger.error(f"Interpretability logging failed: {str(e)}")
            return False
