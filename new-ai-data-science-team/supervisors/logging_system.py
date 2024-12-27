import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime
import asyncio
from pathlib import Path

from elasticsearch import AsyncElasticsearch
from elasticsearch.exceptions import ElasticsearchException

from config.settings import MONITORING_CONFIG, BASE_DIR
from config.logging_config import log_error, log_event

logger = logging.getLogger(__name__)

class LoggingSystem:
    """
    Centralized logging system with ELK Stack integration.
    Handles log collection, processing, and storage with Elasticsearch.
    """
    def __init__(self):
        self.es_client: Optional[AsyncElasticsearch] = None
        self.log_index_prefix = 'ai_data_science_logs'
        self.log_buffer: list = []
        self.buffer_size = 100
        self.flush_interval = 60  # seconds
        self.log_dir = BASE_DIR / 'logs'
        self.log_dir.mkdir(exist_ok=True)

        # Log rotation settings
        self.max_log_size = 10 * 1024 * 1024  # 10MB
        self.backup_count = 5

    async def start(self):
        """Initialize and start the logging system."""
        try:
            await self._initialize_elasticsearch()
            await self._setup_indices()
            await self._start_log_processing()
            log_event(logger, "logging_system_started", {"status": "success"})
        except Exception as e:
            log_error(logger, e, {"context": "logging_system_startup"})
            raise

    async def _initialize_elasticsearch(self):
        """Initialize Elasticsearch connection."""
        try:
            self.es_client = AsyncElasticsearch([MONITORING_CONFIG['elasticsearch_host']])
            # Test connection
            await self.es_client.ping()
            logger.info("Elasticsearch connection established")
        except Exception as e:
            logger.error(f"Failed to connect to Elasticsearch: {str(e)}")
            raise

    async def _setup_indices(self):
        """Setup Elasticsearch indices with appropriate mappings."""
        index_mappings = {
            f"{self.log_index_prefix}_system": {
                "mappings": {
                    "properties": {
                        "timestamp": {"type": "date"},
                        "level": {"type": "keyword"},
                        "component": {"type": "keyword"},
                        "message": {"type": "text"},
                        "details": {"type": "object"},
                        "host": {"type": "keyword"},
                        "environment": {"type": "keyword"}
                    }
                },
                "settings": {
                    "number_of_shards": 1,
                    "number_of_replicas": 1
                }
            },
            f"{self.log_index_prefix}_application": {
                "mappings": {
                    "properties": {
                        "timestamp": {"type": "date"},
                        "level": {"type": "keyword"},
                        "agent": {"type": "keyword"},
                        "action": {"type": "keyword"},
                        "message": {"type": "text"},
                        "metadata": {"type": "object"},
                        "duration": {"type": "float"}
                    }
                }
            },
            f"{self.log_index_prefix}_metrics": {
                "mappings": {
                    "properties": {
                        "timestamp": {"type": "date"},
                        "metric_name": {"type": "keyword"},
                        "value": {"type": "float"},
                        "tags": {"type": "object"},
                        "unit": {"type": "keyword"}
                    }
                }
            }
        }

        for index_name, mapping in index_mappings.items():
            try:
                if not await self.es_client.indices.exists(index=index_name):
                    await self.es_client.indices.create(
                        index=index_name,
                        body=mapping
                    )
                    logger.info(f"Created Elasticsearch index: {index_name}")
            except Exception as e:
                logger.error(f"Failed to create index {index_name}: {str(e)}")
                raise

    async def _start_log_processing(self):
        """Start background tasks for log processing."""
        processing_tasks = [
            self._process_log_buffer(),
            self._monitor_log_files(),
            self._cleanup_old_logs()
        ]
        await asyncio.gather(*processing_tasks)

    async def log(self, level: str, message: str, context: Dict[str, Any] = None):
        """Log a message with context to Elasticsearch."""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': level.upper(),
            'message': message,
            'context': context or {},
            'host': MONITORING_CONFIG.get('host', 'unknown'),
            'environment': MONITORING_CONFIG.get('environment', 'development')
        }

        self.log_buffer.append(log_entry)
        
        if len(self.log_buffer) >= self.buffer_size:
            await self._flush_buffer()

    async def _flush_buffer(self):
        """Flush the log buffer to Elasticsearch."""
        if not self.log_buffer:
            return

        try:
            actions = []
            for entry in self.log_buffer:
                actions.append({
                    '_index': f"{self.log_index_prefix}_system",
                    '_source': entry
                })

            if actions:
                await self.es_client.bulk(body=actions)
                self.log_buffer.clear()
                logger.debug(f"Flushed {len(actions)} log entries to Elasticsearch")
        except Exception as e:
            logger.error(f"Failed to flush logs to Elasticsearch: {str(e)}")
            # Write to backup file if Elasticsearch is unavailable
            await self._write_to_backup_file(self.log_buffer)
            self.log_buffer.clear()

    async def _process_log_buffer(self):
        """Periodically process and flush the log buffer."""
        while True:
            try:
                await asyncio.sleep(self.flush_interval)
                await self._flush_buffer()
            except Exception as e:
                logger.error(f"Error in log buffer processing: {str(e)}")
                await asyncio.sleep(5)

    async def _monitor_log_files(self):
        """Monitor log files for rotation and cleanup."""
        while True:
            try:
                for log_file in self.log_dir.glob('*.log'):
                    if log_file.stat().st_size > self.max_log_size:
                        await self._rotate_log_file(log_file)
                
                await asyncio.sleep(300)  # Check every 5 minutes
            except Exception as e:
                logger.error(f"Error in log file monitoring: {str(e)}")
                await asyncio.sleep(5)

    async def _rotate_log_file(self, log_file: Path):
        """Rotate a log file when it exceeds the size limit."""
        try:
            # Rotate existing backup files
            for i in range(self.backup_count - 1, 0, -1):
                old_backup = log_file.with_suffix(f'.log.{i}')
                new_backup = log_file.with_suffix(f'.log.{i + 1}')
                if old_backup.exists():
                    old_backup.rename(new_backup)

            # Rotate current log file
            if log_file.exists():
                log_file.rename(log_file.with_suffix('.log.1'))

            # Create new empty log file
            log_file.touch()
            logger.info(f"Rotated log file: {log_file}")
        except Exception as e:
            logger.error(f"Error rotating log file {log_file}: {str(e)}")

    async def _cleanup_old_logs(self):
        """Clean up old log files and Elasticsearch indices."""
        while True:
            try:
                # Clean up old backup files
                for log_file in self.log_dir.glob('*.log.*'):
                    if int(log_file.suffix.split('.')[-1]) > self.backup_count:
                        log_file.unlink()

                # Clean up old Elasticsearch indices
                await self._cleanup_old_indices()

                await asyncio.sleep(86400)  # Run once per day
            except Exception as e:
                logger.error(f"Error in log cleanup: {str(e)}")
                await asyncio.sleep(3600)  # Retry in an hour

    async def _cleanup_old_indices(self):
        """Clean up old Elasticsearch indices."""
        try:
            # Get list of indices
            indices = await self.es_client.indices.get(index=f"{self.log_index_prefix}_*")
            
            # Sort indices by creation date
            sorted_indices = sorted(
                indices.items(),
                key=lambda x: x[1]['settings']['index']['creation_date']
            )

            # Keep only the last 30 days of indices
            indices_to_delete = sorted_indices[:-30]
            for index_name, _ in indices_to_delete:
                await self.es_client.indices.delete(index=index_name)
                logger.info(f"Deleted old index: {index_name}")
        except Exception as e:
            logger.error(f"Error cleaning up old indices: {str(e)}")

    async def _write_to_backup_file(self, logs: list):
        """Write logs to a backup file when Elasticsearch is unavailable."""
        backup_file = self.log_dir / 'elasticsearch_backup.log'
        try:
            with backup_file.open('a') as f:
                for log_entry in logs:
                    f.write(json.dumps(log_entry) + '\n')
            logger.info(f"Wrote {len(logs)} logs to backup file")
        except Exception as e:
            logger.error(f"Failed to write to backup file: {str(e)}")

    async def shutdown(self):
        """Gracefully shutdown the logging system."""
        try:
            # Flush remaining logs
            await self._flush_buffer()
            
            # Close Elasticsearch connection
            if self.es_client:
                await self.es_client.close()
            
            logger.info("Logging system shutdown complete")
        except Exception as e:
            logger.error(f"Error during logging system shutdown: {str(e)}")

# Create singleton instance
logging_system = LoggingSystem()
