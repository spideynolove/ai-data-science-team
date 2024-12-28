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

class ModelInterpreter:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.mongo_client = MongoClient(settings.MONGODB_URI)
        self.postgres_client = MongoClient(settings.POSTGRES_URI)
        mlflow.set_tracking_uri(settings.EXPERIMENT_TRACKING_URI)

    async def explain_global(self, model, data: pd.DataFrame) -> Dict[str, Any]:
        """Provide global model explanations"""
        try:
            # SHAP global explanation
            explainer = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(data)
            
            return {
                "shap": {
                    "global_feature_importance": np.abs(shap_values).mean(axis=0).tolist(),
                    "expected_value": explainer.expected_value
                }
            }
        except Exception as e:
            self.logger.error(f"Global explanation failed: {str(e)}")
            return {}

    async def explain_local(self, model, data: pd.DataFrame, instance_index: int) -> Dict[str, Any]:
        """Provide local explanations for a specific instance"""
        try:
            # SHAP local explanation
            explainer = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(data.iloc[instance_index:instance_index+1])
            
            # LIME explanation
            lime_explainer = lime.lime_tabular.LimeTabularExplainer(
                data.values,
                feature_names=data.columns.tolist(),
                class_names=['0', '1'],
                verbose=True,
                mode='classification'
            )
            lime_exp = lime_explainer.explain_instance(
                data.iloc[instance_index].values,
                model.predict_proba,
                num_features=5
            )
            
            return {
                "shap": {
                    "shap_values": shap_values[0].tolist(),
                    "base_value": explainer.expected_value
                },
                "lime": lime_exp.as_list()
            }
        except Exception as e:
            self.logger.error(f"Local explanation failed: {str(e)}")
            return {}

    async def explain_decision_boundary(self, model, data: pd.DataFrame) -> Dict[str, Any]:
        """Explain model decision boundaries"""
        try:
            # Use SHAP to explain decision boundaries
            explainer = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(data)
            
            return {
                "decision_boundary": {
                    "shap_values": shap_values,
                    "expected_value": explainer.expected_value
                }
            }
        except Exception as e:
            self.logger.error(f"Decision boundary explanation failed: {str(e)}")
            return {}

    async def generate_interpretation_report(self, model, data: pd.DataFrame) -> Dict[str, Any]:
        """Generate comprehensive interpretation report"""
        try:
            global_explanation = await self.explain_global(model, data)
            local_explanation = await self.explain_local(model, data, 0)  # First instance
            decision_boundary = await self.explain_decision_boundary(model, data)
            
            return {
                "global": global_explanation,
                "local": local_explanation,
                "decision_boundary": decision_boundary
            }
        except Exception as e:
            self.logger.error(f"Interpretation report generation failed: {str(e)}")
            return {}

    async def log_interpretation(self, run_id: str, interpretation_results: Dict[str, Any]) -> bool:
        """Log interpretation results in MLflow"""
        try:
            with mlflow.start_run(run_id=run_id):
                mlflow.log_dict(interpretation_results, "interpretation.json")
            return True
        except Exception as e:
            self.logger.error(f"Interpretation logging failed: {str(e)}")
            return False
