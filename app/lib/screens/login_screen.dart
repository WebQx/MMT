import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/app_state_provider.dart';
import '../services/auth_service.dart';
import '../services/oauth_service.dart';
import '../utils/constants.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({Key? key}) : super(key: key);

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  bool _isLoading = false;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [
              Constants.primaryColor,
              Constants.secondaryColor,
            ],
          ),
        ),
        child: SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(Constants.padding * 2),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                // Logo and Title
                const Icon(
                  Icons.mic,
                  size: 80,
                  color: Colors.white,
                ),
                const SizedBox(height: 24),
                const Text(
                  'MMT',
                  style: TextStyle(
                    fontSize: 48,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                  ),
                ),
                const SizedBox(height: 8),
                const Text(
                  'Multilingual Medical Transcription',
                  style: TextStyle(
                    fontSize: 16,
                    color: Colors.white70,
                  ),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 48),
                
                // Login Buttons
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(Constants.padding * 2),
                    child: Column(
                      children: [
                        const Text(
                          'Choose Login Method',
                          style: TextStyle(
                            fontSize: 20,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        const SizedBox(height: 24),
                        
                        // OAuth Buttons Row
                        Wrap(
                          spacing: 12,
                          runSpacing: 12,
                          children: [
                            ElevatedButton.icon(
                              onPressed: _isLoading ? null : () => _oauth('google'),
                              icon: const Icon(Icons.g_mobiledata),
                              label: const Text('Google'),
                            ),
                            ElevatedButton.icon(
                              onPressed: _isLoading ? null : () => _oauth('microsoft'),
                              icon: const Icon(Icons.window),
                              label: const Text('Microsoft'),
                            ),
                            ElevatedButton.icon(
                              onPressed: _isLoading ? null : () => _oauth('apple'),
                              icon: const Icon(Icons.apple),
                              label: const Text('Apple'),
                            ),
                          ],
                        ),
                        const SizedBox(height: 24),
                        
                        // Guest Login
                        OutlinedButton.icon(
                          onPressed: _isLoading ? null : _loginAsGuest,
                          icon: const Icon(Icons.person),
                          label: const Text('Continue as Guest'),
                        ),
                        
                        if (_isLoading) ...[
                          const SizedBox(height: 16),
                          const CircularProgressIndicator(),
                        ],
                      ],
                    ),
                  ),
                ),
                
                const SizedBox(height: 32),
                
                // Features List
                const Card(
                  child: Padding(
                    padding: EdgeInsets.all(Constants.padding),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Features',
                          style: TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        SizedBox(height: 12),
                        _FeatureItem(
                          icon: Icons.language,
                          text: 'Multilingual Support',
                        ),
                        _FeatureItem(
                          icon: Icons.cloud,
                          text: 'Cloud & Local Transcription',
                        ),
                        _FeatureItem(
                          icon: Icons.security,
                          text: 'Healthcare-Grade Security',
                        ),
                        _FeatureItem(
                          icon: Icons.integration_instructions,
                          text: 'EHR Integration',
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Future<void> _loginWithKeycloak() async {
    setState(() => _isLoading = true);
    
    try {
      // In a real app, you would integrate with Keycloak OAuth2 flow
      // For demo purposes, we'll simulate a successful login
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Keycloak integration not configured in demo'),
          backgroundColor: Constants.warningColor,
        ),
      );
    } catch (e) {
      _showError('Keycloak login failed: $e');
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _loginAsGuest() async {
    setState(() => _isLoading = true);
    
    try {
      final authService = AuthService();
      final appState = Provider.of<AppStateProvider>(context, listen: false);
      final response = await authService.loginAsGuestWithLanguage(appState.selectedLanguage);
      final token = response['access_token'] as String;
      final offline = response['offline'] as bool? ?? false;

      appState.setAuthenticated(token, 'guest');

      if (offline) {
        // Inform the user they are in offline/demo mode on GitHub Pages.
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Demo mode: running without backend; some features are disabled.'),
            backgroundColor: Constants.warningColor,
            duration: Duration(seconds: 6),
          ),
        );
      }
      
      if (mounted) {
        Navigator.of(context).pushReplacementNamed('/home');
      }
    } catch (e) {
      _showError('Guest login failed: $e');
    } finally {
      setState(() => _isLoading = false);
    }
  }

  void _showError(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Constants.errorColor,
      ),
    );
  }

  Future<void> _oauth(String provider) async {
    setState(() => _isLoading = true);
    try {
      final svc = OAuthService();
      await svc.beginOAuthFlow(provider);
    } catch (e) {
      _showError('OAuth ($provider) start failed: $e');
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }
}

class _FeatureItem extends StatelessWidget {
  final IconData icon;
  final String text;
  
  const _FeatureItem({
    required this.icon,
    required this.text,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          Icon(
            icon,
            size: 20,
            color: Constants.primaryColor,
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Text(text),
          ),
        ],
      ),
    );
  }
}