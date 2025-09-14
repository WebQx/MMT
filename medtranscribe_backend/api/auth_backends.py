"""
Custom Django authentication backend for OpenEMR integration.
Handles PHP-style password verification and session management.
"""

import hashlib
import base64
import json
import pickle
from typing import Optional, Dict, Any
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from .models import OpenEMRUser, OpenEMRSession


class OpenEMRAuthBackend(BaseBackend):
    """
    Authentication backend that validates against OpenEMR's user table
    and handles PHP-style password hashing and session management.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate against OpenEMR users table with PHP password verification
        """
        if username is None or password is None:
            return None
            
        try:
            # Get OpenEMR user
            openemr_user = OpenEMRUser.objects.get(
                username=username,
                active=True
            )
            
            # Verify password using PHP-compatible verification
            if self.verify_php_password(password, openemr_user.password):
                # Create or get Django user
                django_user = self.get_or_create_django_user(openemr_user)
                return django_user
                
        except OpenEMRUser.DoesNotExist:
            # Try guest authentication
            if username == 'guest' and password == 'guest':
                return self.create_guest_user()
                
        return None
    
    def get_user(self, user_id):
        """
        Get user by ID for Django session management
        """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
    
    def verify_php_password(self, password: str, hash_from_db: str) -> bool:
        """
        Verify password against PHP password_hash() generated hash.
        Supports both bcrypt (PASSWORD_DEFAULT) and legacy MD5 hashes.
        """
        # Check if it's a bcrypt hash (modern OpenEMR)
        if hash_from_db.startswith('$2y$') or hash_from_db.startswith('$2a$') or hash_from_db.startswith('$2b$'):
            return self.verify_bcrypt_password(password, hash_from_db)
        
        # Check if it's a legacy MD5 hash (older OpenEMR installations)
        elif len(hash_from_db) == 32:  # MD5 hash length
            return self.verify_md5_password(password, hash_from_db)
        
        # Check if it's a SHA1 hash (some OpenEMR configurations)
        elif len(hash_from_db) == 40:  # SHA1 hash length
            return self.verify_sha1_password(password, hash_from_db)
        
        return False
    
    def verify_bcrypt_password(self, password: str, hash_from_db: str) -> bool:
        """
        Verify bcrypt password (PHP password_hash with PASSWORD_DEFAULT)
        """
        try:
            import bcrypt
            return bcrypt.checkpw(password.encode('utf-8'), hash_from_db.encode('utf-8'))
        except ImportError:
            # Fallback to passlib if bcrypt not available
            try:
                from passlib.hash import bcrypt
                return bcrypt.verify(password, hash_from_db)
            except ImportError:
                return False
    
    def verify_md5_password(self, password: str, hash_from_db: str) -> bool:
        """
        Verify legacy MD5 password hash
        """
        password_hash = hashlib.md5(password.encode('utf-8')).hexdigest()
        return password_hash == hash_from_db
    
    def verify_sha1_password(self, password: str, hash_from_db: str) -> bool:
        """
        Verify SHA1 password hash
        """
        password_hash = hashlib.sha1(password.encode('utf-8')).hexdigest()
        return password_hash == hash_from_db
    
    def get_or_create_django_user(self, openemr_user: OpenEMRUser) -> User:
        """
        Create or update Django user based on OpenEMR user data
        """
        try:
            # Try to get existing Django user
            django_user = User.objects.get(username=openemr_user.username)
            
            # Update user info from OpenEMR
            django_user.email = openemr_user.email or ''
            django_user.first_name = openemr_user.fname or ''
            django_user.last_name = openemr_user.lname or ''
            django_user.is_active = openemr_user.active
            django_user.save()
            
        except User.DoesNotExist:
            # Create new Django user
            django_user = User.objects.create_user(
                username=openemr_user.username,
                email=openemr_user.email or '',
                first_name=openemr_user.fname or '',
                last_name=openemr_user.lname or '',
                is_active=openemr_user.active
            )
        
        # Store OpenEMR user ID in Django user profile (optional)
        if hasattr(django_user, 'profile'):
            django_user.profile.openemr_user_id = openemr_user.id
            django_user.profile.save()
        
        return django_user
    
    def create_guest_user(self) -> User:
        """
        Create or get guest user for unauthenticated access
        """
        try:
            guest_user = User.objects.get(username='guest')
        except User.DoesNotExist:
            guest_user = User.objects.create_user(
                username='guest',
                email='guest@example.com',
                first_name='Guest',
                last_name='User',
                is_active=True
            )
        
        return guest_user
    
    def validate_php_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Validate and parse PHP session data from OpenEMR sessions table
        """
        try:
            session = OpenEMRSession.objects.get(session_id=session_id)
            
            # Parse PHP session data
            session_data = self.parse_php_session(session.session_data)
            
            # Check if session contains valid user authentication
            if 'authUser' in session_data and session_data['authUser']:
                return {
                    'username': session_data.get('authUser'),
                    'user_id': session_data.get('authUserID'),
                    'facility': session_data.get('authProvider'),
                    'session_data': session_data
                }
                
        except OpenEMRSession.DoesNotExist:
            pass
        
        return None
    
    def parse_php_session(self, session_data: str) -> Dict[str, Any]:
        """
        Parse PHP session data format.
        PHP sessions use a specific serialization format.
        """
        try:
            # Try to parse as PHP serialized data
            return self.php_unserialize(session_data)
        except:
            # Fallback: try to find key-value pairs in the session string
            return self.parse_session_fallback(session_data)
    
    def php_unserialize(self, data: str) -> Dict[str, Any]:
        """
        Basic PHP unserialize implementation for session data.
        This is a simplified version that handles common cases.
        """
        result = {}
        
        # Simple regex-based parsing for basic PHP session format
        import re
        
        # Match pattern like: key_name|s:5:"value";
        pattern = r'(\w+)\|([^;]+);'
        matches = re.findall(pattern, data)
        
        for key, value in matches:
            # Parse different PHP types
            if value.startswith('s:'):
                # String: s:5:"hello"
                match = re.match(r's:(\d+):"([^"]*)"', value)
                if match:
                    result[key] = match.group(2)
            elif value.startswith('i:'):
                # Integer: i:123
                match = re.match(r'i:(\d+)', value)
                if match:
                    result[key] = int(match.group(1))
            elif value.startswith('b:'):
                # Boolean: b:1 or b:0
                match = re.match(r'b:([01])', value)
                if match:
                    result[key] = bool(int(match.group(1)))
        
        return result
    
    def parse_session_fallback(self, session_data: str) -> Dict[str, Any]:
        """
        Fallback session parsing for when PHP unserialize fails
        """
        result = {}
        
        # Look for common OpenEMR session variables
        if 'authUser' in session_data:
            # Try to extract user info with regex
            import re
            
            user_match = re.search(r'authUser["|\']\s*:\s*["\']([^"\']+)', session_data)
            if user_match:
                result['authUser'] = user_match.group(1)
            
            id_match = re.search(r'authUserID["|\']\s*:\s*["\']?(\d+)', session_data)
            if id_match:
                result['authUserID'] = int(id_match.group(1))
        
        return result


class SessionAuthMiddleware:
    """
    Middleware to handle OpenEMR PHP session authentication
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.auth_backend = OpenEMRAuthBackend()
    
    def __call__(self, request):
        # Check for OpenEMR session cookie
        openemr_session_id = request.COOKIES.get('OpenEMR', None)
        
        if openemr_session_id and not request.user.is_authenticated:
            # Try to authenticate using OpenEMR session
            session_data = self.auth_backend.validate_php_session(openemr_session_id)
            
            if session_data:
                # Get Django user for the OpenEMR user
                try:
                    openemr_user = OpenEMRUser.objects.get(
                        username=session_data['username'],
                        active=True
                    )
                    django_user = self.auth_backend.get_or_create_django_user(openemr_user)
                    
                    # Manually set the user for this request
                    request.user = django_user
                    
                except OpenEMRUser.DoesNotExist:
                    pass
        
        response = self.get_response(request)
        return response