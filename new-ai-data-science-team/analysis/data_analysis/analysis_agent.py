import pandas as pd
import numpy as np
from typing import Dict, Any
import logging
from pymongo import MongoClient
from config import settings
import statsmodels.api as sm
from scipy import stats
import plotly.express as px

class AnalysisAgent:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.mongo_client = MongoClient(settings.MONGODB_URI)
        self.postgres_client = MongoClient(settings.POSTGRES_URI)

    async def perform_statistical_tests(self, df: pd.DataFrame, test_config: Dict[str, Any]) -> Dict[str, Any]:
        """Perform statistical tests based on configuration"""
        results = {}
        try:
            # Perform t-tests
            if "t_tests" in test_config:
                for test in test_config["t_tests"]:
                    group1 = df[df[test["group_column"]] == test["group1"]][test["value_column"]]
                    group2 = df[df[test["group_column"]] == test["group2"]][test["value_column"]]
                    t_stat, p_value = stats.ttest_ind(group1, group2)
                    results[f"t_test_{test['group1']}_vs_{test['group2']}"] = {
                        "t_statistic": t_stat,
                        "p_value": p_value
                    }
            
            # Perform ANOVA
            if "anova" in test_config:
                for test in test_config["anova"]:
                    groups = [df[df[test["group_column"]] == group][test["value_column"]]
                             for group in df[test["group_column"]].unique()]
                    f_stat, p_value = stats.f_oneway(*groups)
                    results[f"anova_{test['group_column']}"] = {
                        "f_statistic": f_stat,
                        "p_value": p_value
                    }
            
            # Perform regression analysis
            if "regression" in test_config:
                for test in test_config["regression"]:
                    X = df[test["independent_vars"]]
                    X = sm.add_constant(X)
                    y = df[test["dependent_var"]]
                    model = sm.OLS(y, X).fit()
                    results[f"regression_{test['dependent_var']}"] = model.summary().as_text()
            
            return results
            
        except Exception as e:
            self.logger.error(f"Statistical analysis failed: {str(e)}")
            return {}

    async def create_visualizations(self, df: pd.DataFrame, viz_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create visualizations based on configuration"""
        visualizations = {}
        try:
            # Create scatter plots
            if "scatter_plots" in viz_config:
                for plot in viz_config["scatter_plots"]:
                    fig = px.scatter(df, x=plot["x"], y=plot["y"], color=plot.get("color"))
                    visualizations[f"scatter_{plot['x']}_vs_{plot['y']}"] = fig.to_json()
            
            # Create histograms
            if "histograms" in viz_config:
                for hist in viz_config["histograms"]:
                    fig = px.histogram(df, x=hist["column"], nbins=hist.get("bins", 30))
                    visualizations[f"histogram_{hist['column']}"] = fig.to_json()
            
            # Create box plots
            if "box_plots" in viz_config:
                for box in viz_config["box_plots"]:
                    fig = px.box(df, x=box.get("x"), y=box["y"], color=box.get("color"))
                    visualizations[f"box_plot_{box['y']}"] = fig.to_json()
            
            return visualizations
            
        except Exception as e:
            self.logger.error(f"Visualization creation failed: {str(e)}")
            return {}

    async def generate_report(self, df: pd.DataFrame, report_config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive analysis report"""
        try:
            report = {
                "statistics": df.describe().to_dict(),
                "tests": await self.perform_statistical_tests(df, report_config.get("tests", {})),
                "visualizations": await self.create_visualizations(df, report_config.get("visualizations", {}))
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"Report generation failed: {str(e)}")
            return {}
