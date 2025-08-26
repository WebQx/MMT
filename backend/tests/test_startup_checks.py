"""Tests for production startup validation checks."""
import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open

from startup_checks import (
    validate_audit_logging,
    validate_encryption_settings,
    validate_tls_configuration,
    validate_database_configuration,
    validate_external_services,
    run_all_startup_checks
)


class TestAuditLogging:
    def test_dev_environment_no_validation(self):
        """Test that dev environment doesn't require audit logging."""
        with patch.dict(os.environ, {"ENV": "dev"}, clear=False):
            # Should not raise any exception
            validate_audit_logging()
    
    def test_prod_environment_requires_audit_log_file(self):
        """Test that production requires AUDIT_LOG_FILE."""
        with patch.dict(os.environ, {"ENV": "prod"}, clear=False):
            with patch("startup_checks.get_settings") as mock_settings:
                mock_settings.return_value.audit_log_file = None
                
                with pytest.raises(RuntimeError, match="AUDIT_LOG_FILE is mandatory"):
                    validate_audit_logging()
    
    def test_prod_environment_validates_audit_directory(self):
        """Test that production validates audit log directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            audit_file = os.path.join(tmpdir, "audit", "test.log")
            
            with patch.dict(os.environ, {"ENV": "prod"}, clear=False):
                with patch("startup_checks.get_settings") as mock_settings:
                    mock_settings.return_value.audit_log_file = audit_file
                    
                    # Should create directory and validate
                    validate_audit_logging()
                    
                    # Check that directory was created
                    assert Path(audit_file).parent.exists()


class TestEncryptionSettings:
    def test_dev_environment_no_validation(self):
        """Test that dev environment doesn't validate encryption."""
        with patch.dict(os.environ, {"ENV": "dev"}, clear=False):
            validate_encryption_settings()
    
    def test_prod_encryption_disabled_no_validation(self):
        """Test that production with encryption disabled doesn't validate."""
        with patch.dict(os.environ, {"ENV": "prod"}, clear=False):
            with patch("startup_checks.get_settings") as mock_settings:
                mock_settings.return_value.enable_field_encryption = False
                
                validate_encryption_settings()
    
    def test_prod_encryption_enabled_requires_keys(self):
        """Test that production with encryption enabled requires keys."""
        with patch.dict(os.environ, {"ENV": "prod"}, clear=False):
            with patch("startup_checks.get_settings") as mock_settings:
                mock_settings.return_value.enable_field_encryption = True
                mock_settings.return_value.encryption_keys = None
                mock_settings.return_value.primary_encryption_key_id = None
                
                with pytest.raises(RuntimeError, match="ENCRYPTION_KEYS must be provided"):
                    validate_encryption_settings()
    
    def test_prod_encryption_validates_key_format(self):
        """Test that production validates encryption key format."""
        import base64
        valid_key = base64.b64encode(b"A" * 32).decode()  # 32-byte key
        
        with patch.dict(os.environ, {"ENV": "prod"}, clear=False):
            with patch("startup_checks.get_settings") as mock_settings:
                mock_settings.return_value.enable_field_encryption = True
                mock_settings.return_value.encryption_keys = f"key1:{valid_key}"
                mock_settings.return_value.primary_encryption_key_id = "key1"
                
                # Should not raise
                validate_encryption_settings()


class TestTLSConfiguration:
    def test_dev_environment_no_validation(self):
        """Test that dev environment doesn't validate TLS."""
        with patch.dict(os.environ, {"ENV": "dev"}, clear=False):
            validate_tls_configuration()
    
    def test_prod_environment_warns_no_tls(self):
        """Test that production warns when TLS not configured."""
        with patch.dict(os.environ, {"ENV": "prod", "SSL_CERT_FILE": "", "SSL_KEY_FILE": ""}, clear=False):
            # Should not raise, but would log warning
            validate_tls_configuration()
    
    def test_prod_environment_validates_cert_files(self):
        """Test that production validates certificate files exist."""
        with patch.dict(os.environ, {"ENV": "prod", "SSL_CERT_FILE": "/nonexistent/cert.pem", "SSL_KEY_FILE": "/nonexistent/key.pem"}, clear=False):
            with pytest.raises(RuntimeError, match="SSL certificate file not found"):
                validate_tls_configuration()


class TestDatabaseConfiguration:
    def test_dev_environment_no_validation(self):
        """Test that dev environment doesn't validate database."""
        with patch.dict(os.environ, {"ENV": "dev"}, clear=False):
            validate_database_configuration()
    
    def test_prod_environment_rejects_sqlite(self):
        """Test that production rejects SQLite."""
        with patch.dict(os.environ, {"ENV": "prod", "DATABASE_URL": "sqlite:///test.db"}, clear=False):
            with pytest.raises(RuntimeError, match="SQLite database not allowed"):
                validate_database_configuration()
    
    def test_prod_environment_accepts_mysql(self):
        """Test that production accepts MySQL."""
        with patch.dict(os.environ, {"ENV": "prod", "DATABASE_URL": "mysql://user:pass@host/db"}, clear=False):
            validate_database_configuration()
    
    def test_prod_environment_accepts_postgresql(self):
        """Test that production accepts PostgreSQL."""
        with patch.dict(os.environ, {"ENV": "prod", "DATABASE_URL": "postgresql://user:pass@host/db"}, clear=False):
            validate_database_configuration()


class TestExternalServices:
    def test_dev_environment_no_validation(self):
        """Test that dev environment doesn't validate external services."""
        with patch.dict(os.environ, {"ENV": "dev"}, clear=False):
            validate_external_services()
    
    def test_prod_environment_warns_default_rabbitmq(self):
        """Test that production warns about default RabbitMQ."""
        with patch.dict(os.environ, {"ENV": "prod"}, clear=False):
            with patch("startup_checks.get_settings") as mock_settings:
                mock_settings.return_value.rabbitmq_url = "amqp://guest:guest@localhost:5672/"
                mock_settings.return_value.redis_url = None
                
                # Should not raise, but would log warning
                validate_external_services()


class TestRunAllStartupChecks:
    def test_successful_startup_checks(self):
        """Test that all startup checks run successfully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            audit_file = os.path.join(tmpdir, "audit.log")
            
            with patch.dict(os.environ, {
                "ENV": "prod",
                "DATABASE_URL": "mysql://user:pass@host/db",
                "AUDIT_LOG_FILE": audit_file
            }, clear=False):
                with patch("startup_checks.get_settings") as mock_settings:
                    mock_settings.return_value.audit_log_file = audit_file
                    mock_settings.return_value.enable_field_encryption = False
                    mock_settings.return_value.rabbitmq_url = "amqp://user:pass@external-rabbit:5672/"
                    mock_settings.return_value.redis_url = None
                    
                    # Should not raise
                    run_all_startup_checks()
    
    def test_failed_startup_checks_propagate_error(self):
        """Test that failed startup checks propagate errors."""
        with patch.dict(os.environ, {"ENV": "prod"}, clear=False):
            with patch("startup_checks.get_settings") as mock_settings:
                mock_settings.return_value.audit_log_file = None
                
                with pytest.raises(RuntimeError):
                    run_all_startup_checks()