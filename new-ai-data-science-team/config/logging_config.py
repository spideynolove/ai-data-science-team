import logging.config
import os
from typing import Dict, Any
from pathlib import Path

from .settings import MONITORING_CONFIG, BASE_DIR

# Ensure logs directory exists
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

def get_logging_config() -> Dict[str, Any]:
    """
    Returns the logging configuration dictionary.
    Configures logging to file, console, and ELK stack.
    """
    return {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
            },
            'json': {
                'class': 'pythonjsonlogger.jsonlogger.JsonFormatter',
                'format': '%(asctime)s %(levelname)s %(name)s %(message)s'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'standard',
                'level': 'INFO',
                'stream': 'ext://sys.stdout'
            },
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'standard',
                'level': 'DEBUG',
                'filename': str(LOGS_DIR / 'app.log'),
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5
            },
            'error_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'formatter': 'standard',
                'level': 'ERROR',
                'filename': str(LOGS_DIR / 'error.log'),
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5
            },
            'logstash': {
                'class': 'logstash_async.handler.AsynchronousLogstashHandler',
                'formatter': 'json',
                'host': MONITORING_CONFIG['logstash_host'].split('://')[1].split(':')[0],
                'port': int(MONITORING_CONFIG['logstash_host'].split(':')[-1]),
                'database_path': str(LOGS_DIR / 'logstash_queue.db'),
                'transport': 'logstash_async.transport.TcpTransport',
                'ssl_enable': False,
                'ssl_verify': False,
            }
        },
        'loggers': {
            '': {  # Root logger
                'handlers': ['console', 'file', 'error_file', 'logstash'],
                'level': os.getenv('LOG_LEVEL', 'INFO'),
                'propagate': True
            },
            'supervisors': {
                'handlers': ['console', 'file', 'error_file', 'logstash'],
                'level': 'INFO',
                'propagate': False
            },
            'data': {
                'handlers': ['console', 'file', 'error_file', 'logstash'],
                'level': 'INFO',
                'propagate': False
            },
            'processing': {
                'handlers': ['console', 'file', 'error_file', 'logstash'],
                'level': 'INFO',
                'propagate': False
            },
            'analysis': {
                'handlers': ['console', 'file', 'error_file', 'logstash'],
                'level': 'INFO',
                'propagate': False
            }
        }
    }

def setup_logging():
    """
    Initialize logging configuration
    """
    config = get_logging_config()
    logging.config.dictConfig(config)
    
    # Create logger instance
    logger = logging.getLogger(__name__)
    logger.info('Logging system initialized')
    
    return logger

# Utility functions for logging
def log_error(logger: logging.Logger, error: Exception, context: Dict[str, Any] = None):
    """
    Log an error with context information
    """
    error_details = {
        'error_type': type(error).__name__,
        'error_message': str(error),
        'context': context or {}
    }
    logger.error(f"Error occurred: {error_details}", exc_info=True)

def log_metric(logger: logging.Logger, metric_name: str, value: float, tags: Dict[str, str] = None):
    """
    Log a metric with optional tags
    """
    metric_data = {
        'metric_name': metric_name,
        'value': value,
        'tags': tags or {}
    }
    logger.info(f"Metric recorded: {metric_data}")

def log_event(logger: logging.Logger, event_name: str, details: Dict[str, Any] = None):
    """
    Log an event with details
    """
    event_data = {
        'event_name': event_name,
        'details': details or {}
    }
    logger.info(f"Event occurred: {event_data}")

# Initialize logging when module is imported
logger = setup_logging()
