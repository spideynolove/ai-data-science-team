from pathlib import Path
from typing import Dict, Any
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Environment settings
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')

# Database settings
DATABASE_CONFIG = {
    'mongodb': {
        'uri': os.getenv('MONGODB_URI'),
        'user': os.getenv('MONGO_USER'),
        'password': os.getenv('MONGO_PASSWORD'),
    },
    'postgresql': {
        'uri': os.getenv('POSTGRES_URI'),
        'user': os.getenv('POSTGRES_USER'),
        'password': os.getenv('POSTGRES_PASSWORD'),
        'database': os.getenv('POSTGRES_DB'),
    },
    'redis': {
        'uri': os.getenv('REDIS_URI'),
        'ttl': int(os.getenv('CACHE_TTL', 900)),
    }
}

# Monitoring settings
MONITORING_CONFIG = {
    'sentry_dsn': os.getenv('SENTRY_DSN'),
    'prometheus_pushgateway': os.getenv('PROMETHEUS_PUSHGATEWAY'),
    'elasticsearch_host': os.getenv('ELASTICSEARCH_HOST'),
    'logstash_host': os.getenv('LOGSTASH_HOST'),
    'kibana_host': os.getenv('KIBANA_HOST'),
}

# ML settings
ML_CONFIG = {
    'model_registry_path': os.getenv('MODEL_REGISTRY_PATH', '/app/models'),
    'feature_store_path': os.getenv('FEATURE_STORE_PATH', '/app/features'),
    'experiment_tracking_uri': os.getenv('EXPERIMENT_TRACKING_URI'),
}

# Performance settings
PERFORMANCE_CONFIG = {
    'batch_size': int(os.getenv('BATCH_SIZE', 1000)),
    'max_workers': int(os.getenv('MAX_WORKERS', 4)),
    'cache_ttl': int(os.getenv('CACHE_TTL', 900)),
}

# Security settings
SECURITY_CONFIG = {
    'jwt_secret_key': os.getenv('JWT_SECRET_KEY'),
    'jwt_algorithm': os.getenv('JWT_ALGORITHM', 'HS256'),
    'access_token_expire_minutes': int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', 30)),
}

# API settings
API_CONFIG = {
    'rate_limit_calls': int(os.getenv('RATE_LIMIT_CALLS', 100)),
    'rate_limit_period': int(os.getenv('RATE_LIMIT_PERIOD', 3600)),
}

# Feature flags
FEATURE_FLAGS = {
    'enable_ml_pipeline': os.getenv('ENABLE_ML_PIPELINE', 'True').lower() == 'true',
    'enable_real_time_processing': os.getenv('ENABLE_REAL_TIME_PROCESSING', 'True').lower() == 'true',
    'enable_caching': os.getenv('ENABLE_CACHING', 'True').lower() == 'true',
    'enable_monitoring': os.getenv('ENABLE_MONITORING', 'True').lower() == 'true',
}

# Resource limits
RESOURCE_LIMITS = {
    'max_memory_usage': int(os.getenv('MAX_MEMORY_USAGE', 4096)),  # MB
    'max_cpu_usage': int(os.getenv('MAX_CPU_USAGE', 80)),  # Percentage
    'max_storage_usage': int(os.getenv('MAX_STORAGE_USAGE', 10240)),  # MB
}

def get_config() -> Dict[str, Any]:
    """Return all configuration settings."""
    return {
        'debug': DEBUG,
        'environment': ENVIRONMENT,
        'database': DATABASE_CONFIG,
        'monitoring': MONITORING_CONFIG,
        'ml': ML_CONFIG,
        'performance': PERFORMANCE_CONFIG,
        'security': SECURITY_CONFIG,
        'api': API_CONFIG,
        'feature_flags': FEATURE_FLAGS,
        'resource_limits': RESOURCE_LIMITS,
    }
