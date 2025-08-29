"""Production startup validation checks.

Validates critical configuration and environment settings
required for production deployment.
"""
from __future__ import annotations

import os
import ssl
import socket
import structlog
from pathlib import Path
from config import get_settings

logger = structlog.get_logger(__name__)


def validate_audit_logging() -> None:
    """Enforce mandatory audit logging in production."""
    settings = get_settings()
    env = os.environ.get("ENV", os.environ.get("ENVIRONMENT_NAME", "dev"))
    
    if env == 'prod':
        if not settings.audit_log_file:
            raise RuntimeError("AUDIT_LOG_FILE is mandatory in production environment")
        
        # Ensure the directory exists and is writable
        audit_path = Path(settings.audit_log_file)
        audit_dir = audit_path.parent
        
        try:
            audit_dir.mkdir(parents=True, exist_ok=True)
            # Test write access
            test_file = audit_dir / ".audit_test"
            test_file.touch()
            test_file.unlink()
            logger.info("audit_logging_validated", path=settings.audit_log_file)
        except Exception as e:
            raise RuntimeError(f"Audit log directory not writable: {audit_dir}") from e


def validate_encryption_settings() -> None:
    """Validate encryption configuration in production."""
    settings = get_settings()
    env = os.environ.get("ENV", os.environ.get("ENVIRONMENT_NAME", "dev"))
    
    if env == 'prod' and settings.enable_field_encryption:
        if not settings.encryption_keys:
            raise RuntimeError("ENCRYPTION_KEYS must be provided when field encryption is enabled in production")
        
        if not settings.primary_encryption_key_id:
            raise RuntimeError("PRIMARY_ENCRYPTION_KEY_ID must be provided when field encryption is enabled in production")
        
        # Parse and validate encryption keys format
        try:
            key_pairs = settings.encryption_keys.split(',')
            keys_dict = {}
            for pair in key_pairs:
                if ':' not in pair:
                    raise ValueError(f"Invalid key format: {pair}")
                key_id, key_b64 = pair.split(':', 1)
                keys_dict[key_id.strip()] = key_b64.strip()
            
            if settings.primary_encryption_key_id not in keys_dict:
                raise RuntimeError(f"Primary encryption key ID '{settings.primary_encryption_key_id}' not found in ENCRYPTION_KEYS")
            
            # Validate key length (should be base64 encoded 32-byte keys)
            import base64
            primary_key = keys_dict[settings.primary_encryption_key_id]
            decoded_key = base64.b64decode(primary_key)
            if len(decoded_key) != 32:
                raise RuntimeError(f"Primary encryption key must be 32 bytes (256-bit), got {len(decoded_key)} bytes")
                
            logger.info("encryption_validated", 
                       key_count=len(keys_dict), 
                       primary_key_id=settings.primary_encryption_key_id)
                       
        except Exception as e:
            raise RuntimeError(f"Invalid encryption configuration: {e}") from e


def validate_tls_configuration() -> None:
    """Validate TLS/SSL configuration in production."""
    env = os.environ.get("ENV", os.environ.get("ENVIRONMENT_NAME", "dev"))
    
    if env == 'prod':
        # Check if TLS environment variables are set
        ssl_cert = os.environ.get("SSL_CERT_FILE")
        ssl_key = os.environ.get("SSL_KEY_FILE")
        
        if not ssl_cert and not ssl_key:
            logger.warning("tls_not_configured",
                         message="TLS certificates not configured for production. Consider setting SSL_CERT_FILE and SSL_KEY_FILE")
            return
        
        if ssl_cert and ssl_key:
            # Validate certificate files exist and are readable
            cert_path = Path(ssl_cert)
            key_path = Path(ssl_key)
            
            if not cert_path.exists():
                raise RuntimeError(f"SSL certificate file not found: {ssl_cert}")
            
            if not key_path.exists():
                raise RuntimeError(f"SSL key file not found: {ssl_key}")
            
            # Basic certificate validation
            try:
                # Check if certificate file can be loaded
                with open(cert_path, 'r') as f:
                    cert_content = f.read()
                    if "BEGIN CERTIFICATE" not in cert_content:
                        raise ValueError("Invalid certificate format")
                
                # Check if key file can be loaded
                with open(key_path, 'r') as f:
                    key_content = f.read()
                    if "BEGIN PRIVATE KEY" not in key_content and "BEGIN RSA PRIVATE KEY" not in key_content:
                        raise ValueError("Invalid private key format")
                
                logger.info("tls_validated", 
                           cert_file=ssl_cert,
                           key_file=ssl_key)
                           
            except Exception as e:
                raise RuntimeError(f"TLS certificate validation failed: {e}") from e


def validate_database_configuration() -> None:
    """Ensure production database configuration is appropriate."""
    env = os.environ.get("ENV", os.environ.get("ENVIRONMENT_NAME", "dev"))
    
    if env == 'prod':
        database_url = os.environ.get("DATABASE_URL", "")
        
        # Prohibit SQLite in production
        if not database_url or database_url.startswith("sqlite"):
            raise RuntimeError("SQLite database not allowed in production. Configure MySQL or PostgreSQL via DATABASE_URL")
        
        # Ensure MySQL/PostgreSQL is configured
        if not (database_url.startswith("mysql") or database_url.startswith("postgresql")):
            raise RuntimeError("Production requires MySQL or PostgreSQL database. Current DATABASE_URL not supported.")
        
        logger.info("database_validated", database_type=database_url.split("://")[0])


def validate_external_services() -> None:
    """Validate external service configurations for production."""
    settings = get_settings()
    env = os.environ.get("ENV", os.environ.get("ENVIRONMENT_NAME", "dev"))
    
    if env == 'prod':
        # Validate RabbitMQ URL format
        if not settings.rabbitmq_url or settings.rabbitmq_url.startswith("amqp://guest:guest@localhost"):
            logger.warning("rabbitmq_production_config",
                         message="Using default RabbitMQ credentials in production. Consider using external RabbitMQ service")
        
        # Validate Redis configuration for production
        if settings.redis_url and settings.redis_url.startswith("redis://localhost"):
            logger.warning("redis_production_config",
                         message="Using localhost Redis in production. Consider using external Redis service")
        
        logger.info("external_services_validated")


def run_all_startup_checks() -> None:
    """Run all production startup validation checks."""
    logger.info("startup_checks_begin")
    
    try:
        validate_audit_logging()
        validate_encryption_settings() 
        validate_tls_configuration()
        validate_database_configuration()
        validate_external_services()
        
        logger.info("startup_checks_complete", status="success")
        
    except Exception as e:
        logger.error("startup_checks_failed", error=str(e))
        raise


if __name__ == "__main__":  # pragma: no cover
    run_all_startup_checks()
