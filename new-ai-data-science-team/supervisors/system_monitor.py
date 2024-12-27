import asyncio
import logging
import psutil
from typing import Dict, Any, List
from datetime import datetime
import os

from prometheus_client import (
    start_http_server,
    Counter,
    Gauge,
    Histogram,
    REGISTRY,
    CollectorRegistry,
    push_to_gateway
)

from config.settings import get_config, MONITORING_CONFIG
from config.logging_config import log_metric, log_error, log_event
from config.db_config import health_check

logger = logging.getLogger(__name__)

class SystemMonitor:
    """
    System monitoring with Prometheus metrics collection and Grafana integration.
    Monitors system resources, application performance, and pipeline metrics.
    """
    def __init__(self):
        self.config = get_config()
        self.registry = CollectorRegistry()
        self._setup_metrics()
        self.monitoring_interval = 15  # seconds

    def _setup_metrics(self):
        """Initialize Prometheus metrics."""
        # System Metrics
        self.cpu_usage = Gauge(
            'system_cpu_usage',
            'CPU usage percentage',
            registry=self.registry
        )
        self.memory_usage = Gauge(
            'system_memory_usage',
            'Memory usage in MB',
            registry=self.registry
        )
        self.disk_usage = Gauge(
            'system_disk_usage',
            'Disk usage percentage',
            registry=self.registry
        )

        # Application Metrics
        self.pipeline_latency = Histogram(
            'pipeline_latency_seconds',
            'Pipeline processing latency',
            buckets=(1, 5, 10, 30, 60, 120, 300),
            registry=self.registry
        )
        self.pipeline_errors = Counter(
            'pipeline_errors_total',
            'Total pipeline errors',
            ['stage'],
            registry=self.registry
        )
        self.active_agents = Gauge(
            'active_agents',
            'Number of active agents',
            ['agent_type'],
            registry=self.registry
        )

        # Database Metrics
        self.db_connections = Gauge(
            'database_connections',
            'Active database connections',
            ['database'],
            registry=self.registry
        )
        self.db_latency = Histogram(
            'database_operation_latency_seconds',
            'Database operation latency',
            ['database', 'operation'],
            buckets=(0.1, 0.5, 1.0, 2.0, 5.0),
            registry=self.registry
        )

        # Cache Metrics
        self.cache_hits = Counter(
            'cache_hits_total',
            'Total cache hits',
            registry=self.registry
        )
        self.cache_misses = Counter(
            'cache_misses_total',
            'Total cache misses',
            registry=self.registry
        )

        # Model Metrics
        self.model_prediction_latency = Histogram(
            'model_prediction_latency_seconds',
            'Model prediction latency',
            ['model_name'],
            buckets=(0.01, 0.05, 0.1, 0.5, 1.0),
            registry=self.registry
        )
        self.model_accuracy = Gauge(
            'model_accuracy',
            'Model accuracy score',
            ['model_name'],
            registry=self.registry
        )

    async def start(self):
        """Start the monitoring system."""
        try:
            # Start Prometheus HTTP server
            start_http_server(9090)
            logger.info("Started Prometheus metrics server on port 9090")

            # Start monitoring tasks
            monitoring_tasks = [
                self._monitor_system_metrics(),
                self._monitor_application_metrics(),
                self._monitor_database_metrics(),
                self._push_metrics()
            ]
            await asyncio.gather(*monitoring_tasks)
        except Exception as e:
            log_error(logger, e, {"context": "monitor_startup"})
            raise

    async def _monitor_system_metrics(self):
        """Collect system resource metrics."""
        while True:
            try:
                # CPU Usage
                cpu_percent = psutil.cpu_percent(interval=1)
                self.cpu_usage.set(cpu_percent)
                log_metric(logger, "cpu_usage", cpu_percent)

                # Memory Usage
                memory = psutil.virtual_memory()
                memory_mb = memory.used / (1024 * 1024)  # Convert to MB
                self.memory_usage.set(memory_mb)
                log_metric(logger, "memory_usage", memory_mb)

                # Disk Usage
                disk = psutil.disk_usage('/')
                self.disk_usage.set(disk.percent)
                log_metric(logger, "disk_usage", disk.percent)

                # Check resource limits
                await self._check_resource_limits({
                    'cpu': cpu_percent,
                    'memory': memory_mb,
                    'disk': disk.percent
                })

                await asyncio.sleep(self.monitoring_interval)
            except Exception as e:
                log_error(logger, e, {"context": "system_metrics_collection"})
                await asyncio.sleep(5)

    async def _monitor_application_metrics(self):
        """Collect application-specific metrics."""
        while True:
            try:
                # Pipeline metrics
                pipeline_metrics = await self._get_pipeline_metrics()
                for stage, metrics in pipeline_metrics.items():
                    self.pipeline_latency.observe(metrics['latency'])
                    if metrics.get('errors', 0) > 0:
                        self.pipeline_errors.labels(stage=stage).inc(metrics['errors'])

                # Agent metrics
                agent_status = await self._get_agent_status()
                for agent_type, count in agent_status.items():
                    self.active_agents.labels(agent_type=agent_type).set(count)

                await asyncio.sleep(self.monitoring_interval)
            except Exception as e:
                log_error(logger, e, {"context": "application_metrics_collection"})
                await asyncio.sleep(5)

    async def _monitor_database_metrics(self):
        """Collect database performance metrics."""
        while True:
            try:
                # Check database health
                db_status = await health_check()
                for db_name, status in db_status.items():
                    self.db_connections.labels(database=db_name).set(1 if status else 0)

                # Collect database metrics
                db_metrics = await self._get_database_metrics()
                for db_name, metrics in db_metrics.items():
                    self.db_latency.labels(
                        database=db_name,
                        operation='query'
                    ).observe(metrics['query_latency'])

                await asyncio.sleep(self.monitoring_interval)
            except Exception as e:
                log_error(logger, e, {"context": "database_metrics_collection"})
                await asyncio.sleep(5)

    async def _push_metrics(self):
        """Push metrics to Prometheus Pushgateway."""
        while True:
            try:
                push_to_gateway(
                    MONITORING_CONFIG['prometheus_pushgateway'],
                    job='ai_data_science_team',
                    registry=self.registry
                )
                await asyncio.sleep(60)  # Push every minute
            except Exception as e:
                log_error(logger, e, {"context": "metrics_push"})
                await asyncio.sleep(5)

    async def _check_resource_limits(self, metrics: Dict[str, float]):
        """Check if resource usage exceeds defined limits."""
        limits = self.config['resource_limits']
        
        for resource, value in metrics.items():
            limit_key = f'max_{resource}_usage'
            if limit_key in limits and value > limits[limit_key]:
                await self._handle_resource_warning(resource, value, limits[limit_key])

    async def _handle_resource_warning(self, resource: str, value: float, limit: float):
        """Handle resource usage warnings."""
        warning_details = {
            'resource': resource,
            'current_value': value,
            'limit': limit,
            'timestamp': datetime.now().isoformat()
        }
        log_event(logger, "resource_warning", warning_details)

    async def _get_pipeline_metrics(self) -> Dict[str, Dict[str, float]]:
        """Collect pipeline performance metrics."""
        # Implement pipeline metric collection
        return {
            'collection': {'latency': 0.0, 'errors': 0},
            'processing': {'latency': 0.0, 'errors': 0},
            'analysis': {'latency': 0.0, 'errors': 0}
        }

    async def _get_agent_status(self) -> Dict[str, int]:
        """Get status of all agents in the system."""
        # Implement agent status collection
        return {
            'data_collection': 0,
            'processing': 0,
            'analysis': 0
        }

    async def _get_database_metrics(self) -> Dict[str, Dict[str, float]]:
        """Collect database performance metrics."""
        # Implement database metric collection
        return {
            'mongodb': {'query_latency': 0.0},
            'postgresql': {'query_latency': 0.0},
            'redis': {'query_latency': 0.0}
        }

    def record_model_metrics(self, model_name: str, prediction_time: float, accuracy: float):
        """Record model performance metrics."""
        self.model_prediction_latency.labels(model_name=model_name).observe(prediction_time)
        self.model_accuracy.labels(model_name=model_name).set(accuracy)

    def record_cache_metrics(self, hit: bool):
        """Record cache hit/miss metrics."""
        if hit:
            self.cache_hits.inc()
        else:
            self.cache_misses.inc()

# Create singleton instance
system_monitor = SystemMonitor()
