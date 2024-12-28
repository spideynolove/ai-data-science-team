import pandas as pd
import numpy as np
from typing import List, Dict, Any
import logging
from pymongo import MongoClient
from config import settings
from feature_engine import creation
from sklearn.preprocessing import PolynomialFeatures
from sklearn.decomposition import PCA

class FeatureGenerator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.mongo_client = MongoClient(settings.MONGODB_URI)
        self.postgres_client = MongoClient(settings.POSTGRES_URI)

    async def generate_polynomial_features(self, df: pd.DataFrame, degree: int = 2) -> pd.DataFrame:
        """Generate polynomial features"""
        try:
            poly = PolynomialFeatures(degree=degree, include_bias=False)
            poly_features = poly.fit_transform(df.select_dtypes(include=np.number))
            feature_names = poly.get_feature_names_out(df.columns)
            return pd.DataFrame(poly_features, columns=feature_names)
        except Exception as e:
            self.logger.error(f"Polynomial feature generation failed: {str(e)}")
            return pd.DataFrame()

    async def generate_pca_features(self, df: pd.DataFrame, n_components: int = 2) -> pd.DataFrame:
        """Generate PCA features"""
        try:
            pca = PCA(n_components=n_components)
            pca_features = pca.fit_transform(df.select_dtypes(include=np.number))
            return pd.DataFrame(pca_features, columns=[f"pca_{i}" for i in range(n_components)])
        except Exception as e:
            self.logger.error(f"PCA feature generation failed: {str(e)}")
            return pd.DataFrame()

    async def generate_categorical_features(self, df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
        """Generate categorical features"""
        try:
            for feature_config in config:
                if feature_config["type"] == "one_hot":
                    df = pd.get_dummies(df, columns=[feature_config["column"]], prefix=feature_config.get("prefix"))
                elif feature_config["type"] == "target_encoding":
                    encoder = creation.MeanEncoder(variables=[feature_config["column"]])
                    df = encoder.fit_transform(df, df[feature_config["target"]])
            return df
        except Exception as e:
            self.logger.error(f"Categorical feature generation failed: {str(e)}")
            return df

    async def generate_features(self, df: pd.DataFrame, generation_config: Dict[str, Any]) -> pd.DataFrame:
        """Generate features based on configuration"""
        try:
            # Generate polynomial features
            if generation_config.get("polynomial", False):
                poly_df = await self.generate_polynomial_features(
                    df,
                    degree=generation_config["polynomial"].get("degree", 2)
                )
                df = pd.concat([df, poly_df], axis=1)
            
            # Generate PCA features
            if generation_config.get("pca", False):
                pca_df = await self.generate_pca_features(
                    df,
                    n_components=generation_config["pca"].get("n_components", 2)
                )
                df = pd.concat([df, pca_df], axis=1)
            
            # Generate categorical features
            if generation_config.get("categorical", False):
                df = await self.generate_categorical_features(
                    df,
                    generation_config["categorical"]
                )
            
            return df
            
        except Exception as e:
            self.logger.error(f"Feature generation failed: {str(e)}")
            return df

    async def version_features(self, df: pd.DataFrame, version: str) -> bool:
        """Version features in feature store"""
        try:
            if df.empty:
                self.logger.warning("Empty dataframe, nothing to version")
                return False
                
            # Add version column
            df["feature_version"] = version
            
            # Store versioned features
            db = self.postgres_client.get_database()
            collection = db["feature_versions"]
            collection.insert_many(df.to_dict('records'))
            
            return True
            
        except Exception as e:
            self.logger.error(f"Feature versioning failed: {str(e)}")
            return False
