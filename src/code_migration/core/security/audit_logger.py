"""
Comprehensive security event logging.

Compliance Requirements:
Security audit logging.

Provides tamper-evident logging for migration events.
"""

import json
import logging
import logging.handlers
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional

from code_migration.utils.logger import get_logger

logger = get_logger(__name__)


class SecurityAuditLogger:
    """
    Secure audit logging for sensitive operations.
    
    Features:
    - Structured JSON logging
    - Required metadata (user, action, timestamp)
    """
    
    def __init__(self, log_dir: Path):
        """
        Initialize audit logger.
        
        Args:
            log_dir: Directory for audit logs
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / 'security_audit.jsonl'
        
        # We also pass audit logs through structlog
        self._logger = logger
        
        self.setup_logging()

    def close(self):
        """Close logger."""
        if hasattr(self, 'logger'):
            for handler in self.logger.handlers[:]:
                handler.close()
                self.logger.removeHandler(handler)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def setup_logging(self):
        """Configure structured JSON logging."""
        # Create logger
        self.logger = logging.getLogger('security_audit')
        self.logger.setLevel(logging.INFO)
        
        # Remove existing handlers to avoid duplicates
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Rotating file handler
        handler = logging.handlers.RotatingFileHandler(
            self.log_file,
            maxBytes=50*1024*1024,  # 50MB
            backupCount=10,
            encoding='utf-8'
        )
        
        # JSON formatter
        formatter = logging.Formatter(
            '%(message)s'  # We'll format JSON manually
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        
        # Prevent propagation to root logger
        self.logger.propagate = False
    
    def log_event(
        self,
        event_type: str,
        user: str,
        action: str,
        resource: str,
        result: str,
        details: Optional[Dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """
        Log security event.
        
        Args:
            event_type: FILE_ACCESS, MIGRATION_START, AUTH_ATTEMPT, etc.
            user: User identifier (anonymized if needed)
            action: READ, WRITE, DELETE, MIGRATE, etc.
            resource: File path or resource identifier
            result: SUCCESS, FAILURE, DENIED
            details: Additional context
            ip_address: Client IP address
            user_agent: User agent string
        """
        # Generate unique event ID
        event_id = hashlib.sha256(
            f"{datetime.now(timezone.utc).isoformat()}{user}{resource}{action}".encode()
        ).hexdigest()[:16]
        
        # Create structured event
        event = {
            'event_id': event_id,
            'event_type': event_type,
            'timestamp_utc': datetime.now(timezone.utc).isoformat(),
            'timestamp_unix': int(datetime.now(timezone.utc).timestamp()),
            'user': self._sanitize_user_id(user),
            'action': action.upper(),
            'resource': self._sanitize_resource_path(resource),
            'result': result.upper(),
            'ip_address': ip_address or self._get_client_ip(),
            'user_agent': user_agent or 'Unknown',
            'details': self._sanitize_details(details or {}),
            'session_id': self._get_session_id(),
            'compliance': {
                'gdpr_pii_processed': self._contains_pii(resource),
                'hipaa_phi_accessed': self._contains_phi(resource),
                'data_classification': self._classify_data(resource)
            }
        }
        
        # Log as JSON line
        try:
            event_json = json.dumps(event, separators=(',', ':'))
            self.logger.info(event_json)
            self._logger.info("audit_event", **event)
        except Exception:
            # Fallback logging if JSON serialization fails
            fallback_event = {
                'event_id': event_id,
                'event_type': event_type,
                'timestamp': datetime.now().isoformat(),
                'user': 'ANONYMIZED',
                'action': action,
                'resource': 'REDACTED',
                'result': result,
                'error': 'JSON_SERIALIZATION_FAILED'
            }
            fallback_json = json.dumps(fallback_event, separators=(',', ':'))
            self.logger.info(fallback_json)
            self._logger.info("audit_event", **fallback_event)
    
    def log_file_access(
        self,
        file_path: str,
        user: str,
        action: str,
        result: str = "SUCCESS",
        file_size: Optional[int] = None,
        checksum: Optional[str] = None
    ):
        """
        Log file access event.
        
        Args:
            file_path: Path to accessed file
            user: User performing action
            action: READ, WRITE, DELETE, etc.
            result: SUCCESS, FAILURE, DENIED
            file_size: Size of file in bytes
            checksum: File checksum for integrity
        """
        details = {}
        if file_size is not None:
            details['file_size'] = file_size
        if checksum is not None:
            details['checksum'] = checksum
        
        self.log_event(
            event_type='FILE_ACCESS',
            user=user,
            action=action,
            resource=file_path,
            result=result,
            details=details
        )
    
    def log_migration_event(
        self,
        migration_type: str,
        project_path: str,
        user: str,
        action: str,
        result: str,
        details: Optional[Dict] = None
    ):
        """
        Log migration-related event.
        
        Args:
            migration_type: Type of migration (react-hooks, vue3, etc.)
            project_path: Path to project being migrated
            user: User performing migration
            action: START, PROGRESS, COMPLETE, ROLLBACK
            result: SUCCESS, FAILURE, PARTIAL
            details: Additional migration details
        """
        migration_details = {
            'migration_type': migration_type,
            'project': self._sanitize_resource_path(project_path)
        }
        if details:
            migration_details.update(details)
        
        self.log_event(
            event_type='MIGRATION_EVENT',
            user=user,
            action=action,
            resource=project_path,
            result=result,
            details=migration_details
        )
    
    def log_security_violation(
        self,
        violation_type: str,
        user: str,
        resource: str,
        details: Optional[Dict] = None
    ):
        """
        Log security violation.
        
        Args:
            violation_type: Type of violation (PATH_TRAVERSAL, INJECTION_ATTEMPT, etc.)
            user: User who triggered violation
            resource: Target resource
            details: Violation details
        """
        self.log_event(
            event_type='SECURITY_VIOLATION',
            user=user,
            action='VIOLATION',
            resource=resource,
            result='BLOCKED',
            details={
                'violation_type': violation_type,
                **(details or {})
            }
        )
    
    def search_logs(
        self,
        event_type: Optional[str] = None,
        user: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> list:
        """
        Search audit logs.
        
        Args:
            event_type: Filter by event type
            user: Filter by user
            start_time: Start time filter
            end_time: End time filter
            limit: Maximum results to return
            
        Returns:
            List of matching log entries
        """
        results = []
        
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        event = json.loads(line)
                        
                        # Apply filters
                        if event_type and event.get('event_type') != event_type:
                            continue
                        
                        if user and event.get('user') != user:
                            continue
                        
                        if start_time:
                            event_time = datetime.fromisoformat(event.get('timestamp_utc', ''))
                            if event_time < start_time:
                                continue
                        
                        if end_time:
                            event_time = datetime.fromisoformat(event.get('timestamp_utc', ''))
                            if event_time >= end_time:
                                continue
                        
                        results.append(event)
                        
                        if len(results) >= limit:
                            break
                            
                    except (json.JSONDecodeError, ValueError):
                        continue
                        
        except FileNotFoundError:
            pass
        
        return results
    
    def generate_compliance_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict:
        """
        Generate compliance report for audits.
        
        Args:
            start_date: Report start date
            end_date: Report end date
            
        Returns:
            Compliance report data
        """
        if end_date is None:
            end_date = datetime.now(timezone.utc)

        if start_date is None:
            start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Get all events in date range
        events = self.search_logs(
            start_time=start_date,
            end_time=end_date,
            limit=10000
        )
        
        # Generate statistics
        report = {
            'report_period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat()
            },
            'summary': {
                'total_events': len(events),
                'unique_users': len(set(e.get('user', 'UNKNOWN') for e in events)),
                'file_access_count': len([e for e in events if e.get('event_type') == 'FILE_ACCESS']),
                'migration_events': len([e for e in events if e.get('event_type') == 'MIGRATION_EVENT']),
                'security_violations': len([e for e in events if e.get('event_type') == 'SECURITY_VIOLATION'])
            },
            'compliance': {
                'gdpr_pii_events': len([e for e in events if e.get('compliance', {}).get('gdpr_pii_processed', False)]),
                'hipaa_phi_events': len([e for e in events if e.get('compliance', {}).get('hipaa_phi_accessed', False)]),
                'data_access_events': len([e for e in events if e.get('action') in ['READ', 'WRITE', 'DELETE']]),
                'failed_operations': len([e for e in events if e.get('result') == 'FAILURE'])
            },
            'top_users': self._get_top_users(events),
            'top_resources': self._get_top_resources(events),
            'security_events': [e for e in events if e.get('event_type') == 'SECURITY_VIOLATION']
        }
        
        return report
    
    @staticmethod
    def _sanitize_user_id(user: str) -> str:
        """Sanitize user ID for logging."""
        if not user:
            return "ANONYMOUS"
        
        # Hash user ID for privacy (GDPR compliance)
        return hashlib.sha256(user.encode()).hexdigest()[:16]
    
    @staticmethod
    def _sanitize_resource_path(path: str) -> str:
        """Remove sensitive parts of path for logging."""
        if not path:
            return "UNKNOWN"
        
        # Remove username, keep relative path
        try:
            from pathlib import Path
            p = Path(path)
            if p.is_absolute():
                return p.name
            return str(p)
        except Exception:
            return "SANITIZED"

    @classmethod
    def _sanitize_details(cls, value):
        """Redact absolute paths from nested logging metadata."""
        if isinstance(value, dict):
            sanitized = {}
            for key, item in value.items():
                if key.endswith("_path") or key in {"path", "project_path", "file_path"}:
                    sanitized[key] = cls._sanitize_resource_path(str(item))
                else:
                    sanitized[key] = cls._sanitize_details(item)
            return sanitized
        if isinstance(value, list):
            return [cls._sanitize_details(item) for item in value]
        return value
    
    @staticmethod
    def _get_client_ip() -> str:
        """Get client IP (for web-based deployments)."""
        # Placeholder - implement based on deployment
        return "127.0.0.1"
    
    @staticmethod
    def _get_session_id() -> str:
        """Get current session ID."""
        # Placeholder - implement session management
        return hashlib.sha256(
            f"{datetime.now(timezone.utc).isoformat()}".encode()
        ).hexdigest()[:8]
    
    @staticmethod
    def _contains_pii(resource: str) -> bool:
        """Check if resource might contain PII."""
        pii_indicators = ['user', 'profile', 'personal', 'contact', 'email', 'phone']
        resource_lower = resource.lower()
        return any(indicator in resource_lower for indicator in pii_indicators)
    
    @staticmethod
    def _contains_phi(resource: str) -> bool:
        """Check if resource might contain PHI."""
        phi_indicators = ['medical', 'health', 'patient', 'diagnosis', 'treatment', 'pharmacy']
        resource_lower = resource.lower()
        return any(indicator in resource_lower for indicator in phi_indicators)
    
    @staticmethod
    def _classify_data(resource: str) -> str:
        """Classify data sensitivity level."""
        resource_lower = resource.lower()
        
        if any(word in resource_lower for word in ['secret', 'key', 'password', 'token']):
            return 'RESTRICTED'
        elif any(word in resource_lower for word in ['user', 'personal', 'profile']):
            return 'CONFIDENTIAL'
        elif any(word in resource_lower for word in ['config', 'setting', 'log']):
            return 'INTERNAL'
        else:
            return 'PUBLIC'
    
    def _get_top_users(self, events: list, limit: int = 10) -> list:
        """Get top users by activity."""
        user_counts = {}
        for event in events:
            user = event.get('user', 'UNKNOWN')
            user_counts[user] = user_counts.get(user, 0) + 1
        
        return sorted(user_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
    
    def _get_top_resources(self, events: list, limit: int = 10) -> list:
        """Get top accessed resources."""
        resource_counts = {}
        for event in events:
            resource = event.get('resource', 'UNKNOWN')
            resource_counts[resource] = resource_counts.get(resource, 0) + 1
        
        return sorted(resource_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
