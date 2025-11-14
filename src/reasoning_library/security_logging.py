"""
Security Logging Module for Reasoning Library

MAJOR-006: Comprehensive security logging for monitoring and auditing.

This module provides centralized security event logging that addresses
insufficient logging for security monitoring vulnerabilities.

Features:
1. Security event detection and classification
2. Attack attempt logging with context
3. Audit trail maintenance
4. Rate limiting and correlation
5. Log injection prevention
6. Sensitive data protection
"""

import logging
import hashlib
import time
import json
import re
import threading
from typing import Dict, Any, Optional, List, Set
from datetime import datetime, timezone
from enum import Enum
from contextlib import contextmanager

# Security event classification
class SecurityEventType(Enum):
    """Classification of security events for proper monitoring."""
    CODE_INJECTION = "code_injection"
    SQL_INJECTION = "sql_injection"
    XSS_ATTEMPT = "xss_attempt"
    PATH_TRAVERSAL = "path_traversal"
    COMMAND_INJECTION = "command_injection"
    LDAP_INJECTION = "ldap_injection"
    LOG_INJECTION = "log_injection"
    TEMPLATE_INJECTION = "template_injection"
    SIZE_LIMIT_EXCEEDED = "size_limit_exceeded"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    ENCODED_ATTACK = "encoded_attack"
    NESTED_INJECTION = "nested_injection"
    UNICODE_BYPASS = "unicode_bypass"
    SANITIZATION_BLOCKED = "sanitization_blocked"
    VALIDATION_FAILED = "validation_failed"
    AUTHENTICATION_FAILED = "authentication_failed"
    AUTHORIZATION_FAILED = "authorization_failed"
    SUSPICIOUS_PATTERN = "suspicious_pattern"


class SecuritySeverity(Enum):
    """Severity levels for security events."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SecurityLogger:
    """
    Centralized security logging system with event classification and correlation.

    Addresses MAJOR-006: Insufficient logging for security monitoring.
    """

    def __init__(self, logger_name: str = "reasoning_library.security"):
        self.logger = logging.getLogger(logger_name)
        self._lock = threading.Lock()

        # Rate limiting per source IP/client
        self._rate_limit_tracker: Dict[str, List[float]] = {}
        self._rate_limit_window = 300  # 5 minutes
        self._rate_limit_threshold = 100  # events per window

        # Event correlation
        self._event_patterns: Dict[str, Dict[str, Any]] = {}

        # Sensitive patterns to mask in logs
        self._sensitive_patterns = [
            r'password[=:]\s*[\'\"]?([^\'\"\s]+)',
            r'api[_-]?key[=:]\s*[\'\"]?([^\'\"\s]+)',
            r'token[=:]\s*[\'\"]?([^\'\"\s]+)',
            r'secret[=:]\s*[\'\"]?([^\'\"\s]+)',
            r'credential[s]?[=:]\s*[\'\"]?([^\'\"\s]+)',
        ]

        # Attack pattern detection
        self._attack_patterns = {
            SecurityEventType.CODE_INJECTION: [
                r'eval\s*\(', r'exec\s*\(', r'__import__\s*\(',
                r'compile\s*\(', r'getattr\s*\(', r'setattr\s*\(',
                r'delattr\s*\(', r'globals\s*\(\)', r'locals\s*\(\)',
            ],
            SecurityEventType.SQL_INJECTION: [
                r'\bdrop\s+table\b', r'\bdelete\s+from\b', r'\binsert\s+into\b',
                r'\bupdate\s+.*\bset\b', r'\bunion\s+select\b', r'\bexec\s*\(',
                r';\s*(drop|delete|insert|update|create|alter)',
            ],
            SecurityEventType.XSS_ATTEMPT: [
                r'<script[^>]*>', r'</script>', r'javascript:', r'onclick\s*=',
                r'onload\s*=', r'onerror\s*=', r'alert\s*\(', r'confirm\s*\(',
                r'prompt\s*\(', r'document\.cookie', r'window\.location',
            ],
            SecurityEventType.PATH_TRAVERSAL: [
                r'\.\./', r'\.\.\\', r'%2e%2e%2f', r'%2e%2e\\',
                r'\.\.%2f', r'\.\.%5c', r'/etc/passwd', r'\\windows\\system32',
            ],
            SecurityEventType.COMMAND_INJECTION: [
                r';\s*(rm|del|format|net\s+user|cmd|powershell|bash|sh)',
                r'\|\s*(rm|del|format|net\s+user|cmd|powershell|bash|sh)',
                r'&&\s*(rm|del|format|net\s+user|cmd|powershell|bash|sh)',
            ],
            SecurityEventType.LDAP_INJECTION: [
                r'\)\(.*\=', r'\*\)\(', r'\(\|\(', r'\)\|',
                r'jndi:', r'ldap:', r'rmi:',
            ],
            SecurityEventType.LOG_INJECTION: [
                r'\n\[ERROR\]', r'\r\[CRITICAL\]', r'\x0b\[INFO\]',
                r'\n\[WARN\]', r'\r\[DEBUG\]',
            ],
        }

    def _classify_attack(self, input_text: str) -> Optional[SecurityEventType]:
        """Classify the type of attack based on input patterns."""
        input_lower = input_text.lower()

        for event_type, patterns in self._attack_patterns.items():
            for pattern in patterns:
                if re.search(pattern, input_lower, re.IGNORECASE):
                    return event_type

        return SecurityEventType.SUSPICIOUS_PATTERN

    def _determine_severity(self, event_type: SecurityEventType, context: Dict[str, Any]) -> SecuritySeverity:
        """Determine severity level based on event type and context."""
        # Critical severity events
        if event_type in [
            SecurityEventType.CODE_INJECTION,
            SecurityEventType.COMMAND_INJECTION,
            SecurityEventType.RATE_LIMIT_EXCEEDED,
        ]:
            return SecuritySeverity.CRITICAL

        # High severity events
        if event_type in [
            SecurityEventType.SQL_INJECTION,
            SecurityEventType.XSS_ATTEMPT,
            SecurityEventType.NESTED_INJECTION,
        ]:
            return SecuritySeverity.HIGH

        # Medium severity events
        if event_type in [
            SecurityEventType.PATH_TRAVERSAL,
            SecurityEventType.LDAP_INJECTION,
            SecurityEventType.ENCODED_ATTACK,
            SecurityEventType.UNICODE_BYPASS,
        ]:
            return SecuritySeverity.MEDIUM

        # Default to medium for security events
        return SecuritySeverity.MEDIUM

    def _mask_sensitive_data(self, text: str) -> str:
        """Mask sensitive data patterns in log entries."""
        masked_text = text

        for pattern in self._sensitive_patterns:
            masked_text = re.sub(
                pattern,
                lambda m: f"{m.group().split('=')[0]}=***REDACTED***",
                masked_text,
                flags=re.IGNORECASE
            )

        return masked_text

    def _generate_event_id(self, input_text: str, source: str) -> str:
        """Generate unique event ID for correlation."""
        content = f"{input_text}:{source}:{time.time()}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _check_rate_limit(self, source: str) -> bool:
        """Check if source has exceeded rate limits."""
        with self._lock:
            now = time.time()

            # Clean old entries
            if source in self._rate_limit_tracker:
                self._rate_limit_tracker[source] = [
                    timestamp for timestamp in self._rate_limit_tracker[source]
                    if now - timestamp < self._rate_limit_window
                ]
            else:
                self._rate_limit_tracker[source] = []

            # Check current rate
            self._rate_limit_tracker[source].append(now)

            if len(self._rate_limit_tracker[source]) > self._rate_limit_threshold:
                self._rate_limit_tracker[source] = self._rate_limit_tracker[source][-self._rate_limit_threshold:]
                return False  # Rate limit exceeded

            return True  # Within rate limits

    def _create_security_log_entry(self,
                                 event_type: SecurityEventType,
                                 severity: SecuritySeverity,
                                 input_text: str,
                                 source: str = "unknown",
                                 context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create structured security log entry."""
        event_id = self._generate_event_id(input_text, source)

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_id": event_id,
            "event_type": event_type.value,
            "severity": severity.value,
            "source": source,
            "input_preview": self._mask_sensitive_data(input_text[:100]),
            "input_hash": hashlib.sha256(input_text.encode()).hexdigest()[:16],
            "context": context or {},
            "detection_patterns": self._get_detected_patterns(input_text, event_type),
        }

    def _get_detected_patterns(self, input_text: str, event_type: SecurityEventType) -> List[str]:
        """Get the specific patterns that triggered detection."""
        detected = []

        if event_type in self._attack_patterns:
            for pattern in self._attack_patterns[event_type]:
                if re.search(pattern, input_text.lower(), re.IGNORECASE):
                    detected.append(pattern)

        return detected

    def log_security_event(self,
                          input_text: str,
                          source: str = "unknown",
                          context: Optional[Dict[str, Any]] = None,
                          block_action: bool = False) -> Dict[str, Any]:
        """
        Log a security event with full context and classification.

        Args:
            input_text: The suspicious input that triggered the event
            source: Source identifier (IP, user ID, module, etc.)
            context: Additional context information
            block_action: Whether the action was blocked

        Returns:
            Dict containing the log entry details
        """
        # Rate limiting check
        if not self._check_rate_limit(source):
            rate_limit_event = self._create_security_log_entry(
                SecurityEventType.RATE_LIMIT_EXCEEDED,
                SecuritySeverity.CRITICAL,
                f"Rate limit exceeded for source: {source}",
                source,
                {"original_input": self._mask_sensitive_data(input_text[:100])}
            )

            self._write_security_log(rate_limit_event)
            return rate_limit_event

        # Classify the attack
        event_type = self._classify_attack(input_text)
        severity = self._determine_severity(event_type, context or {})

        # Create log entry
        log_entry = self._create_security_log_entry(
            event_type,
            severity,
            input_text,
            source,
            context
        )

        # Add action context
        log_entry["action"] = "blocked" if block_action else "sanitized"

        # Write to logs
        self._write_security_log(log_entry)

        # Update correlation data
        self._update_correlation_data(log_entry)

        return log_entry

    def _write_security_log(self, log_entry: Dict[str, Any]) -> None:
        """Write security log entry to appropriate log levels."""
        severity = log_entry["severity"]
        message = self._format_log_message(log_entry)

        if severity == SecuritySeverity.CRITICAL.value:
            self.logger.critical(message)
        elif severity == SecuritySeverity.HIGH.value:
            self.logger.error(message)
        elif severity == SecuritySeverity.MEDIUM.value:
            self.logger.warning(message)
        else:  # LOW
            self.logger.info(message)

    def _format_log_message(self, log_entry: Dict[str, Any]) -> str:
        """Format log entry into readable message."""
        return (
            f"[SECURITY] {log_entry['event_type'].upper()} | "
            f"Severity: {log_entry['severity'].upper()} | "
            f"Source: {log_entry['source']} | "
            f"Action: {log_entry.get('action', 'unknown')} | "
            f"Event ID: {log_entry['event_id']} | "
            f"Patterns: {', '.join(log_entry['detection_patterns'][:3])}"
        )

    def _update_correlation_data(self, log_entry: Dict[str, Any]) -> None:
        """Update correlation data for attack pattern analysis."""
        with self._lock:
            event_type = log_entry["event_type"]
            source = log_entry["source"]

            if event_type not in self._event_patterns:
                self._event_patterns[event_type] = {}

            if source not in self._event_patterns[event_type]:
                self._event_patterns[event_type][source] = {
                    "count": 0,
                    "first_seen": log_entry["timestamp"],
                    "last_seen": log_entry["timestamp"],
                    "severity_levels": set(),
                }

            # Update statistics
            stats = self._event_patterns[event_type][source]
            stats["count"] += 1
            stats["last_seen"] = log_entry["timestamp"]
            stats["severity_levels"].add(log_entry["severity"])

    def get_security_metrics(self) -> Dict[str, Any]:
        """Get security metrics for monitoring and reporting."""
        with self._lock:
            total_events = sum(
                source_stats["count"]
                for event_type in self._event_patterns.values()
                for source_stats in event_type.values()
            )

            events_by_type = {
                event_type: sum(source_stats["count"] for source_stats in sources.values())
                for event_type, sources in self._event_patterns.items()
            }

            active_sources = set()
            for sources in self._event_patterns.values():
                active_sources.update(sources.keys())

            return {
                "total_events": total_events,
                "events_by_type": events_by_type,
                "active_sources": len(active_sources),
                "rate_limited_sources": len(self._rate_limit_tracker),
                "correlation_patterns": len(self._event_patterns),
                "last_activity": max(
                    (source_stats["last_seen"]
                     for sources in self._event_patterns.values()
                     for source_stats in sources.values()),
                    default=None
                )
            }

    @contextmanager
    def security_context(self, source: str = "unknown"):
        """Context manager for security-aware operations."""
        start_time = time.time()
        try:
            yield self
        except Exception as e:
            # Log unexpected security-relevant exceptions
            if any(keyword in str(e).lower() for keyword in
                  ['security', 'injection', 'attack', 'malicious', 'unauthorized']):
                self.log_security_event(
                    str(e),
                    source=source,
                    context={"exception_type": type(e).__name__, "duration": time.time() - start_time},
                    block_action=True
                )
            raise


# Global security logger instance
_security_logger = SecurityLogger()

def get_security_logger() -> SecurityLogger:
    """Get the global security logger instance."""
    return _security_logger

def log_security_event(input_text: str,
                      source: str = "unknown",
                      context: Optional[Dict[str, Any]] = None,
                      block_action: bool = False) -> Dict[str, Any]:
    """
    Convenience function to log security events.

    Args:
        input_text: The suspicious input
        source: Source identifier
        context: Additional context
        block_action: Whether the action was blocked

    Returns:
        Dict containing the log entry
    """
    return _security_logger.log_security_event(input_text, source, context, block_action)

def get_security_metrics() -> Dict[str, Any]:
    """Get current security metrics."""
    return _security_logger.get_security_metrics()

def setup_security_logging(level: str = "WARNING") -> None:
    """
    Setup security logging with appropriate handlers and formatters.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    logger = logging.getLogger("reasoning_library.security")
    logger.setLevel(getattr(logging, level.upper()))

    # Prevent duplicate handlers
    if not logger.handlers:
        # Console handler
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        # File handler (if possible)
        try:
            file_handler = logging.FileHandler('reasoning_library_security.log')
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(pathname)s:%(lineno)d'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
        except (PermissionError, OSError):
            # File logging not available, continue with console only
            pass


# Setup security logging by default
setup_security_logging()