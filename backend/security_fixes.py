"""Security fixes for production deployment."""

import re
import html
from typing import Any


def sanitize_log_input(value: Any) -> str:
    """Sanitize user input before logging to prevent log injection."""
    if value is None:
        return "None"
    
    # Convert to string and sanitize
    sanitized = str(value)
    
    # Remove or escape newlines and carriage returns
    sanitized = sanitized.replace('\n', '\\n').replace('\r', '\\r')
    
    # Remove control characters
    sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', sanitized)
    
    # HTML escape to prevent XSS in log viewers
    sanitized = html.escape(sanitized)
    
    # Truncate if too long
    if len(sanitized) > 1000:
        sanitized = sanitized[:997] + "..."
    
    return sanitized


def validate_filename(filename: str) -> str:
    """Validate and sanitize filename to prevent path traversal."""
    if not filename:
        raise ValueError("Filename cannot be empty")
    
    # Remove path separators and relative path components
    sanitized = filename.replace('..', '').replace('/', '').replace('\\', '')
    
    # Remove null bytes and control characters
    sanitized = re.sub(r'[\x00-\x1f\x7f]', '', sanitized)
    
    # Ensure filename is not empty after sanitization
    if not sanitized.strip():
        raise ValueError("Invalid filename after sanitization")
    
    return sanitized.strip()


def validate_session_id(session_id: str) -> str:
    """Validate session ID format."""
    if not session_id:
        raise ValueError("Session ID cannot be empty")

    if len(session_id) > 256:
        raise ValueError("Session ID too long")

    if any(ch in session_id for ch in {"\n", "\r", "\x00"}):
        raise ValueError("Invalid control characters in session ID")

    return session_id