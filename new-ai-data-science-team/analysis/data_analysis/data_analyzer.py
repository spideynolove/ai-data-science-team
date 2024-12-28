import pandas as pd
import numpy as np
from typing import Dict, Any
import logging
from pymongo import MongoClient
from config import settings
from scipy.stats import pearsonr, spearmanr
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans

class DataAnalyzer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.mongo_client = MongoClient(settings.MONGODB_URI)
        self.postgres_client = MongoClient(settings.POSTGRES_URI)

    async def calculate_correlations(self, df: pd.DataFrame, method: str = "pearson") -> pd.DataFrame:
        """Calculate correlations between numeric features"""
        try:
            numeric_df = df.select_dtypes(include=np.number)
            if method == "pearson":
                corr_matrix = numeric_df.corr(method=pearsonr)
            elif method == "spearman":
                corr_matrix = numeric_df.corr(method=spearmanr)
            else:
                raise ValueError("Invalid correlation method")
            return corr_matrix
        except Exception as e:
            self.logger.error(f"Correlation calculation failed: {str(e)}")
            return pd.DataFrame()

    async def perform_pca(self, df: pd.DataFrame, n_components: int = 2) -> Dict[str, Any]:
        """Perform Principal Component Analysis"""
        try:
            numeric_df = df.select_dtypes(include=np.number)
            pca = PCA(n_components=n_components)
            components = pca.fit_transform(numeric_df)
            
            return {
                "components": components,
                "explained_variance": pca.explained_variance_ratio_.tolist(),
                "feature_importance": pca.components_.tolist()
            }
        except Exception as e:
            self.logger.error(f"PCA failed: {str(e)}")
            return {}

    async def perform_clustering(self, df: pd.DataFrame, n_clusters: int = 3) -> Dict[str, Any]:
        """Perform K-Means clustering"""
        try:
            numeric_df = df.select_dtypes(include=np.number)
            kmeans = KMeans(n_clusters=n_clusters)
            clusters = kmeans.fit_predict(numeric_df)
            
            return {
                "clusters": clusters.tolist(),
                "centroids": kmeans.cluster_centers_.tolist(),
                "inertia": kmeans.inertia_
            }
        except Exception as e:
            self.logger.error(f"Clustering failed: {str(e)}")
            return {}

    async def analyze_trends(self, df: pd.DataFrame, time_column: str, value_column: str) -> Dict[str, Any]:
        """Analyze time series trends"""
        try:
            df = df.sort_values(time_column)
            rolling_mean = df[value_column].rolling(window=7).mean()
            rolling_std = df[value_column].rolling(window=7).std()
            
            return {
                "trend": df[value_column].values.tolist(),
                "rolling_mean": rolling_mean.values.tolist(),
                "rolling_std": rolling_std.values.tolist()
            }
        except Exception as e:
            self.logger.error(f"Trend analysis failed: {str(e)}")
            return {}

    async def analyze_distribution(self, df: pd.DataFrame, column: str) -> Dict[str, Any]:
        """Analyze feature distribution"""
        try:
            return {
                "mean": df[column].mean(),
                "median": df[column].median(),
                "std": df[column].std(),
                "skewness": df[column].skew(),
                "kurtosis": df[column].kurt()
            }
        except Exception as e:
            self.logger.error(f"Distribution analysis failed: {str(e)}")
            return {}
