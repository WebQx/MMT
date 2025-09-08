import 'package:flutter/material.dart';

class Constants {
  // API Configuration
  static const String baseUrl = 'http://localhost:8000';
  static const String apiVersion = '/api/v1';
  
  // Keycloak Configuration
  static const String keycloakUrl = 'https://your-keycloak-domain/auth';
  static const String keycloakRealm = 'your-realm';
  static const String keycloakClientId = 'mmt-app';
  
  // Supported Languages
  static const List<Locale> supportedLocales = [
    Locale('en', 'US'), // English
    Locale('es', 'ES'), // Spanish
    Locale('fr', 'FR'), // French
    Locale('de', 'DE'), // German
    Locale('ar', 'SA'), // Arabic
    Locale('zh', 'CN'), // Chinese
    Locale('ja', 'JP'), // Japanese
    Locale('ko', 'KR'), // Korean
    Locale('hi', 'IN'), // Hindi
    Locale('pt', 'BR'), // Portuguese
  ];
  
  // Audio Configuration
  static const int maxRecordingDuration = 600; // 10 minutes in seconds
  static const int chunkSizeBytes = 1024 * 1024; // 1MB chunks for upload
  
  // Network Types
  static const List<String> networkModes = [
    'Cellular',
    'WiFi', 
    'Cloud'
  ];
  
  // Transcription Types
  static const List<String> transcriptionTypes = [
    'Real-time Transcription',
    'Record Now, Transcribe Later',
    'Ambient Mode'
  ];
  
  // Supported Audio Formats
  static const List<String> supportedAudioFormats = [
    'wav',
    'mp3',
    'mp4',
    'm4a',
    'flac',
    'ogg'
  ];
  
  // Storage Keys
  static const String authTokenKey = 'auth_token';
  static const String userTypeKey = 'user_type';
  static const String themeKey = 'theme_mode';
  static const String localeKey = 'locale';
  static const String onboardingCompletedKey = 'onboarding_completed';

  // Development helpers
  // When true the app will allow a local/offline guest login flow when the
  // backend is unreachable. This should remain true for local development and
  // false in production deployments.
  static const bool allowOfflineAuth = true;
  static const String offlineGuestTokenPrefix = 'dev-guest-token';
  
  // Error Messages
  static const String networkErrorMessage = 'Network error. Please check your connection.';
  static const String authErrorMessage = 'Authentication failed. Please login again.';
  static const String micPermissionErrorMessage = 'Microphone permission is required for recording.';
  static const String filePermissionErrorMessage = 'File access permission is required.';
  
  // UI Constants
  static const double borderRadius = 12.0;
  static const double padding = 16.0;
  static const double buttonHeight = 48.0;
  
  // Colors
  static const Color primaryColor = Color(0xFF667EEA);
  static const Color secondaryColor = Color(0xFF764BA2);
  static const Color errorColor = Color(0xFFE53E3E);
  static const Color successColor = Color(0xFF38A169);
  static const Color warningColor = Color(0xFFDD6B20);
}