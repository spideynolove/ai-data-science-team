import logging
import traceback
from typing import Dict, Any, Optional, Callable
from datetime import datetime
import asyncio

import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration

from config.settings import MONITORING_CONFIG
from config.logging_config import log_error, log_event

logger = logging.getLogger(__name__)

class ErrorHandler:
    """
    Centralized error handling system with Sentry integration and custom recovery procedures.
    """
    def __init__(self):
        self._initialize_sentry()
        self.error_counts: Dict[str, int] = {}
        self.error_thresholds: Dict[str, int] = {
            'critical': 1,    # Immediate escalation
            'error': 5,       # Escalate after 5 occurrences
            'warning': 10     # Escalate after 10 occurrences
        }
        self.recovery_procedures: Dict[str, Callable] = {}
        self.active_recoveries: Dict[str, datetime] = {}

    def _initialize_sentry(self):
        """Initialize Sentry SDK with custom configurations."""
        sentry_logging = LoggingIntegration(
            level=logging.INFO,        # Capture info and above as breadcrumbs
            event_level=logging.ERROR  # Send errors as events
        )

        sentry_sdk.init(
            dsn=MONITORING_CONFIG['sentry_dsn'],
            traces_sample_rate=1.0,
            environment=MONITORING_CONFIG.get('environment', 'production'),
            integrations=[sentry_logging],
            before_send=self._before_send_event
        )
        logger.info("Sentry initialization completed")

    def _before_send_event(self, event: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Pre-process events before sending to Sentry."""
        if 'exc_info' in hint:
            exc_type, exc_value, tb = hint['exc_info']
            event['fingerprint'] = [
                '{{ default }}',
                str(exc_type),
                str(exc_value),
            ]
        return event

    async def handle_error(self, error: Exception, context: Dict[str, Any] = None) -> bool:
        """
        Main error handling method. Returns True if error was handled successfully.
        """
        try:
            error_type = type(error).__name__
            error_details = {
                'type': error_type,
                'message': str(error),
                'traceback': traceback.format_exc(),
                'context': context or {},
                'timestamp': datetime.now().isoformat()
            }

            # Log the error
            log_error(logger, error, context)

            # Track error count
            self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1

            # Check if recovery is needed
            if await self._should_attempt_recovery(error_type):
                return await self._attempt_recovery(error_type, error_details)

            # Check if escalation is needed
            if self._should_escalate(error_type):
                await self._escalate_error(error_details)

            return True
        except Exception as e:
            logger.error(f"Error in error handler: {str(e)}", exc_info=True)
            return False

    async def _should_attempt_recovery(self, error_type: str) -> bool:
        """Determine if recovery should be attempted for this error type."""
        if error_type not in self.recovery_procedures:
            return False

        last_recovery = self.active_recoveries.get(error_type)
        if last_recovery:
            # Prevent recovery attempts more often than every 5 minutes
            time_since_last = (datetime.now() - last_recovery).total_seconds()
            if time_since_last < 300:  # 5 minutes
                return False

        return True

    async def _attempt_recovery(self, error_type: str, error_details: Dict[str, Any]) -> bool:
        """Attempt to recover from an error using registered recovery procedures."""
        try:
            if error_type in self.recovery_procedures:
                logger.info(f"Attempting recovery for {error_type}")
                self.active_recoveries[error_type] = datetime.now()

                recovery_procedure = self.recovery_procedures[error_type]
                success = await recovery_procedure(error_details)

                if success:
                    log_event(logger, "error_recovery_success", {
                        "error_type": error_type,
                        "details": error_details
                    })
                    self.error_counts[error_type] = 0  # Reset error count
                    return True
                else:
                    log_event(logger, "error_recovery_failed", {
                        "error_type": error_type,
                        "details": error_details
                    })

            return False
        except Exception as e:
            logger.error(f"Error in recovery attempt: {str(e)}", exc_info=True)
            return False

    def _should_escalate(self, error_type: str) -> bool:
        """Determine if an error should be escalated based on frequency and severity."""
        count = self.error_counts.get(error_type, 0)
        
        # Determine error severity
        if 'critical' in error_type.lower():
            threshold = self.error_thresholds['critical']
        elif 'error' in error_type.lower():
            threshold = self.error_thresholds['error']
        else:
            threshold = self.error_thresholds['warning']

        return count >= threshold

    async def _escalate_error(self, error_details: Dict[str, Any]):
        """Escalate an error to appropriate channels."""
        try:
            log_event(logger, "error_escalation", error_details)
            
            # Send to Sentry
            with sentry_sdk.push_scope() as scope:
                scope.set_extras(error_details['context'])
                sentry_sdk.capture_exception()

            # Additional escalation logic could be implemented here
            # (e.g., sending alerts, notifications, etc.)

        except Exception as e:
            logger.error(f"Error in escalation: {str(e)}", exc_info=True)

    def register_recovery_procedure(self, error_type: str, procedure: Callable):
        """Register a recovery procedure for a specific error type."""
        self.recovery_procedures[error_type] = procedure
        logger.info(f"Registered recovery procedure for {error_type}")

    async def monitor_error_patterns(self):
        """
        Continuously monitor error patterns and trigger alerts for unusual patterns.
        """
        while True:
            try:
                current_time = datetime.now()
                
                # Analyze error patterns
                for error_type, count in self.error_counts.items():
                    if count > 0:
                        # Check for error spikes
                        if self._detect_error_spike(error_type, count):
                            await self._handle_error_spike(error_type, count)
                
                # Reset counts periodically
                if current_time.hour == 0 and current_time.minute == 0:
                    self.error_counts.clear()
                
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in pattern monitoring: {str(e)}", exc_info=True)
                await asyncio.sleep(5)

    def _detect_error_spike(self, error_type: str, count: int) -> bool:
        """Detect unusual spikes in error frequency."""
        # Implement error spike detection logic
        return count >= self.error_thresholds.get(error_type, 10)

    async def _handle_error_spike(self, error_type: str, count: int):
        """Handle detected error spikes."""
        try:
            spike_details = {
                'error_type': error_type,
                'count': count,
                'timestamp': datetime.now().isoformat()
            }
            log_event(logger, "error_spike_detected", spike_details)
            
            # Additional spike handling logic could be implemented here
            
        except Exception as e:
            logger.error(f"Error in spike handling: {str(e)}", exc_info=True)

# Create singleton instance
error_handler = ErrorHandler()
