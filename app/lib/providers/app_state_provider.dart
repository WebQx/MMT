import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../utils/constants.dart';

class AppStateProvider extends ChangeNotifier {
  final SharedPreferences _prefs;
  
  AppStateProvider(this._prefs) {
    _loadSettings();
  }
  
  // Authentication state
  bool _isAuthenticated = false;
  String? _authToken;
  String? _userType;
  
  // UI state
  ThemeMode _themeMode = ThemeMode.system;
  Locale _currentLocale = const Locale('en', 'US');
  bool _onboardingCompleted = false;
  
  // Transcription state
  String _selectedTranscriptionType = Constants.transcriptionTypes.first;
  String _selectedNetworkMode = Constants.networkModes[1]; // WiFi default
  bool _ambientModeEnabled = false;
  String _selectedLanguage = 'auto';
  
  // Getters
  bool get isAuthenticated => _isAuthenticated;
  String? get authToken => _authToken;
  String? get userType => _userType;
  ThemeMode get themeMode => _themeMode;
  Locale get currentLocale => _currentLocale;
  bool get onboardingCompleted => _onboardingCompleted;
  String get selectedTranscriptionType => _selectedTranscriptionType;
  String get selectedNetworkMode => _selectedNetworkMode;
  bool get ambientModeEnabled => _ambientModeEnabled;
  String get selectedLanguage => _selectedLanguage;
  
  // Authentication methods
  void setAuthenticated(String token, String type) {
    _isAuthenticated = true;
    _authToken = token;
    _userType = type;
    _prefs.setString(Constants.authTokenKey, token);
    _prefs.setString(Constants.userTypeKey, type);
    notifyListeners();
  }
  
  void logout() {
    _isAuthenticated = false;
    _authToken = null;
    _userType = null;
    _prefs.remove(Constants.authTokenKey);
    _prefs.remove(Constants.userTypeKey);
    notifyListeners();
  }
  
  // Theme methods
  void setThemeMode(ThemeMode mode) {
    _themeMode = mode;
    _prefs.setInt(Constants.themeKey, mode.index);
    notifyListeners();
  }
  
  // Locale methods
  void setLocale(Locale locale) {
    _currentLocale = locale;
    _prefs.setString(Constants.localeKey, '${locale.languageCode}_${locale.countryCode}');
    notifyListeners();
  }
  
  // Onboarding methods
  void setOnboardingCompleted() {
    _onboardingCompleted = true;
    _prefs.setBool(Constants.onboardingCompletedKey, true);
    notifyListeners();
  }
  
  // Transcription settings
  void setTranscriptionType(String type) {
    _selectedTranscriptionType = type;
    notifyListeners();
  }
  
  void setNetworkMode(String mode) {
    _selectedNetworkMode = mode;
    notifyListeners();
  }
  
  void setAmbientMode(bool enabled) {
    _ambientModeEnabled = enabled;
    notifyListeners();
  }
  
  void setLanguage(String language) {
  _selectedLanguage = language;
  // persist the selection
  _prefs.setString('selected_language', language);
  notifyListeners();
  }
  
  // Private methods
  void _loadSettings() {
    // Load authentication state
    _authToken = _prefs.getString(Constants.authTokenKey);
    _userType = _prefs.getString(Constants.userTypeKey);
    _isAuthenticated = _authToken != null;
    
    // Load theme
    final themeIndex = _prefs.getInt(Constants.themeKey) ?? ThemeMode.system.index;
    _themeMode = ThemeMode.values[themeIndex];
    
    // Load locale
    final localeString = _prefs.getString(Constants.localeKey) ?? 'en_US';
    final parts = localeString.split('_');
    if (parts.length == 2) {
      _currentLocale = Locale(parts[0], parts[1]);
    }
    
    // Load onboarding state
    _onboardingCompleted = _prefs.getBool(Constants.onboardingCompletedKey) ?? false;
  // Load selected language
  _selectedLanguage = _prefs.getString('selected_language') ?? _selectedLanguage;
  }
}