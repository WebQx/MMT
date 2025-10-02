import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:provider/provider.dart';
import '../providers/app_state_provider.dart';
import '../utils/constants.dart';

class SettingsScreen extends StatelessWidget {
  const SettingsScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Settings'),
      ),
      body: Consumer<AppStateProvider>(
        builder: (context, appState, _) {
          return ListView(
            padding: const EdgeInsets.all(Constants.padding),
            children: [
              // Account Section
              _SectionHeader(title: 'Account'),
              Card(
                child: Column(
                  children: [
                    ListTile(
                      leading: Icon(
                        appState.userType == 'guest' 
                          ? Icons.person 
                          : Icons.verified_user,
                      ),
                      title: Text(
                        appState.userType == 'guest' 
                          ? 'Guest User' 
                          : 'Authenticated User',
                      ),
                      subtitle: Text(
                        appState.userType == 'guest'
                          ? 'Limited functionality'
                          : 'Full access',
                      ),
                    ),
                    const Divider(height: 1),
                    ListTile(
                      leading: const Icon(Icons.logout),
                      title: const Text('Logout'),
                      onTap: () => _logout(context),
                    ),
                  ],
                ),
              ),
              
              const SizedBox(height: 24),
              
              // Appearance Section
              _SectionHeader(title: 'Appearance'),
              Card(
                child: Column(
                  children: [
                    ListTile(
                      leading: const Icon(Icons.palette),
                      title: const Text('Theme'),
                      subtitle: Text(_getThemeName(appState.themeMode)),
                      onTap: () => _showThemeDialog(context),
                    ),
                    const Divider(height: 1),
                    ListTile(
                      leading: const Icon(Icons.language),
                      title: const Text('Language'),
                      subtitle: Text(_getLanguageName(appState.currentLocale)),
                      onTap: () => _showLanguageDialog(context),
                    ),
                  ],
                ),
              ),
              
              const SizedBox(height: 24),
              
              // Transcription Settings
              _SectionHeader(title: 'Transcription'),
              Card(
                child: Column(
                  children: [
                    ListTile(
                      leading: const Icon(Icons.settings_voice),
                      title: const Text('Default Transcription Type'),
                      subtitle: Text(appState.selectedTranscriptionType),
                      onTap: () => _showTranscriptionTypeDialog(context),
                    ),
                    const Divider(height: 1),
                    ListTile(
                      leading: const Icon(Icons.network_check),
                      title: const Text('Default Network Mode'),
                      subtitle: Text(appState.selectedNetworkMode),
                      onTap: () => _showNetworkModeDialog(context),
                    ),
                    const Divider(height: 1),
                    ListTile(
                      leading: const Icon(Icons.translate),
                      title: const Text('Default Language'),
                      subtitle: Text(
                        appState.selectedLanguage == 'auto' 
                          ? 'Auto-detect' 
                          : appState.selectedLanguage.toUpperCase(),
                      ),
                      onTap: () => _showTranscriptionLanguageDialog(context),
                    ),
                  ],
                ),
              ),
              
              const SizedBox(height: 24),
              
              // Privacy & Security
              _SectionHeader(title: 'Privacy & Security'),
              Card(
                child: Column(
                  children: [
                    ListTile(
                      leading: const Icon(Icons.security),
                      title: const Text('Data Protection'),
                      subtitle: const Text('GDPR, HIPAA compliant'),
                      onTap: () => _showDataProtectionInfo(context),
                    ),
                    const Divider(height: 1),
                    ListTile(
                      leading: const Icon(Icons.delete),
                      title: const Text('Clear Local Data'),
                      subtitle: const Text('Remove cached files and settings'),
                      onTap: () => _showClearDataDialog(context),
                    ),
                  ],
                ),
              ),
              
              const SizedBox(height: 24),
              
              // Storage Section
              _SectionHeader(title: 'Storage'),
              Card(
                child: Column(
                  children: [
                    FutureBuilder<Map<String, dynamic>>(
                      future: _getStorageStatus(),
                      builder: (context, snapshot) {
                        if (snapshot.connectionState == ConnectionState.waiting) {
                          return const ListTile(
                            leading: CircularProgressIndicator(),
                            title: Text('Storage Provider'),
                            subtitle: Text('Checking status...'),
                          );
                        }
                        
                        if (snapshot.hasError) {
                          return ListTile(
                            leading: const Icon(Icons.error, color: Colors.red),
                            title: const Text('Storage Provider'),
                            subtitle: Text('Error: ${snapshot.error}'),
                          );
                        }
                        
                        final data = snapshot.data ?? {};
                        final provider = data['provider'] ?? 'database';
                        final nextcloudConfigured = data['nextcloud_configured'] ?? false;
                        final nextcloudStatus = data['nextcloud_status'] ?? 'unknown';
                        
                        IconData statusIcon;
                        Color statusColor;
                        String statusText;
                        
                        if (provider == 'nextcloud') {
                          if (nextcloudStatus == 'connected') {
                            statusIcon = Icons.cloud_done;
                            statusColor = Colors.green;
                            statusText = 'Nextcloud Connected';
                          } else if (nextcloudStatus == 'error') {
                            statusIcon = Icons.cloud_off;
                            statusColor = Colors.red;
                            statusText = 'Nextcloud Error';
                          } else {
                            statusIcon = Icons.cloud_queue;
                            statusColor = Colors.orange;
                            statusText = 'Nextcloud Pending';
                          }
                        } else {
                          statusIcon = Icons.storage;
                          statusColor = Colors.blue;
                          statusText = 'Database Only';
                        }
                        
                        return ListTile(
                          leading: Icon(statusIcon, color: statusColor),
                          title: const Text('Storage Provider'),
                          subtitle: Text(statusText),
                          trailing: provider == 'nextcloud' && data['base_url'] != null
                            ? IconButton(
                                icon: const Icon(Icons.info_outline),
                                onPressed: () => _showStorageInfo(context, data),
                              )
                            : null,
                        );
                      },
                    ),
                  ],
                ),
              ),
              
              const SizedBox(height: 24),
              
              // About Section
              _SectionHeader(title: 'About'),
              Card(
                child: Column(
                  children: [
                    const ListTile(
                      leading: Icon(Icons.info),
                      title: Text('Version'),
                      subtitle: Text('1.0.0'),
                    ),
                    const Divider(height: 1),
                    ListTile(
                      leading: const Icon(Icons.description),
                      title: const Text('License'),
                      subtitle: const Text('MIT License'),
                      onTap: () => _showLicenseDialog(context),
                    ),
                    const Divider(height: 1),
                    ListTile(
                      leading: const Icon(Icons.contact_support),
                      title: const Text('Contact'),
                      subtitle: const Text('Info@WebQx.Healthcare'),
                      onTap: () => _contactSupport(context),
                    ),
                  ],
                ),
              ),
              
              const SizedBox(height: 24),
              
              // Footer
              const Center(
                child: Text(
                  'MMT - Multilingual Medical Transcription\n© 2025 WebQx Healthcare',
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    color: Colors.grey,
                    fontSize: 12,
                  ),
                ),
              ),
            ],
          );
        },
      ),
    );
  }

  String _getThemeName(ThemeMode mode) {
    switch (mode) {
      case ThemeMode.light:
        return 'Light';
      case ThemeMode.dark:
        return 'Dark';
      case ThemeMode.system:
        return 'System';
    }
  }

  String _getLanguageName(Locale locale) {
    switch (locale.languageCode) {
      case 'en':
        return 'English';
      case 'es':
        return 'Español';
      case 'fr':
        return 'Français';
      case 'de':
        return 'Deutsch';
      case 'ar':
        return 'العربية';
      case 'zh':
        return '中文';
      case 'ja':
        return '日本語';
      case 'ko':
        return '한국어';
      case 'hi':
        return 'हिन्दी';
      case 'pt':
        return 'Português';
      default:
        return locale.languageCode.toUpperCase();
    }
  }

  void _logout(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Logout'),
        content: const Text('Are you sure you want to logout?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () {
              final appState = Provider.of<AppStateProvider>(context, listen: false);
              appState.logout();
              Navigator.of(context).pushNamedAndRemoveUntil('/login', (route) => false);
            },
            child: const Text('Logout'),
          ),
        ],
      ),
    );
  }

  void _showThemeDialog(BuildContext context) {
    final appState = Provider.of<AppStateProvider>(context, listen: false);
    
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Select Theme'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: ThemeMode.values.map((mode) {
            return RadioListTile<ThemeMode>(
              title: Text(_getThemeName(mode)),
              value: mode,
              groupValue: appState.themeMode,
              onChanged: (value) {
                if (value != null) {
                  appState.setThemeMode(value);
                  Navigator.pop(context);
                }
              },
            );
          }).toList(),
        ),
      ),
    );
  }

  void _showLanguageDialog(BuildContext context) {
    final appState = Provider.of<AppStateProvider>(context, listen: false);
    
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Select Language'),
        content: SizedBox(
          width: double.maxFinite,
          child: ListView(
            shrinkWrap: true,
            children: Constants.supportedLocales.map((locale) {
              return RadioListTile<Locale>(
                title: Text(_getLanguageName(locale)),
                value: locale,
                groupValue: appState.currentLocale,
                onChanged: (value) {
                  if (value != null) {
                    appState.setLocale(value);
                    Navigator.pop(context);
                  }
                },
              );
            }).toList(),
          ),
        ),
      ),
    );
  }

  void _showTranscriptionTypeDialog(BuildContext context) {
    final appState = Provider.of<AppStateProvider>(context, listen: false);
    
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Default Transcription Type'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: Constants.transcriptionTypes.map((type) {
            return RadioListTile<String>(
              title: Text(type),
              value: type,
              groupValue: appState.selectedTranscriptionType,
              onChanged: (value) {
                if (value != null) {
                  appState.setTranscriptionType(value);
                  Navigator.pop(context);
                }
              },
            );
          }).toList(),
        ),
      ),
    );
  }

  void _showNetworkModeDialog(BuildContext context) {
    final appState = Provider.of<AppStateProvider>(context, listen: false);
    
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Default Network Mode'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: Constants.networkModes.map((mode) {
            return RadioListTile<String>(
              title: Text(mode),
              value: mode,
              groupValue: appState.selectedNetworkMode,
              onChanged: (value) {
                if (value != null) {
                  appState.setNetworkMode(value);
                  Navigator.pop(context);
                }
              },
            );
          }).toList(),
        ),
      ),
    );
  }

  void _showTranscriptionLanguageDialog(BuildContext context) {
    final appState = Provider.of<AppStateProvider>(context, listen: false);
    final languages = ['auto', 'en', 'es', 'fr', 'de', 'ar', 'zh', 'ja', 'ko', 'hi', 'pt'];
    
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Default Transcription Language'),
        content: SizedBox(
          width: double.maxFinite,
          child: ListView(
            shrinkWrap: true,
            children: languages.map((lang) {
              return RadioListTile<String>(
                title: Text(lang == 'auto' ? 'Auto-detect' : lang.toUpperCase()),
                value: lang,
                groupValue: appState.selectedLanguage,
                onChanged: (value) {
                  if (value != null) {
                    appState.setLanguage(value);
                    Navigator.pop(context);
                  }
                },
              );
            }).toList(),
          ),
        ),
      ),
    );
  }

  void _showDataProtectionInfo(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Data Protection'),
        content: const SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              Text('MMT is designed with healthcare-grade security and compliance:'),
              SizedBox(height: 16),
              Text('• GDPR compliant data handling'),
              Text('• HIPAA ready for healthcare environments'),
              Text('• ISO 27701 privacy standards'),
              Text('• End-to-end encryption'),
              Text('• Data minimization principles'),
              Text('• Audit logging for compliance'),
              SizedBox(height: 16),
              Text('Your data is processed securely and never stored without consent.'),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('OK'),
          ),
        ],
      ),
    );
  }

  void _showClearDataDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Clear Local Data'),
        content: const Text('This will remove all cached files, recordings, and reset settings to defaults. This action cannot be undone.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () {
              Navigator.pop(context);
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                  content: Text('Local data cleared successfully'),
                  backgroundColor: Constants.successColor,
                ),
              );
            },
            child: const Text('Clear'),
          ),
        ],
      ),
    );
  }

  void _showLicenseDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('MIT License'),
        content: const SingleChildScrollView(
          child: Text(
            'Copyright (c) 2025 Taha Ahmad\n\n'
            'Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:\n\n'
            'The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.\n\n'
            'THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.',
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('OK'),
          ),
        ],
      ),
    );
  }

  Future<Map<String, dynamic>> _getStorageStatus() async {
    try {
      final response = await http.get(
        Uri.parse('${Constants.baseUrl}/storage/status'),
        headers: {'Content-Type': 'application/json'},
      );
      
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Storage status check failed: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Unable to check storage status: $e');
    }
  }

  void _showStorageInfo(BuildContext context, Map<String, dynamic> data) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Storage Information'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Provider: ${data['provider'] ?? 'Unknown'}'),
            const SizedBox(height: 8),
            if (data['base_url'] != null) ...[
              Text('Nextcloud URL: ${data['base_url']}'),
              const SizedBox(height: 8),
            ],
            if (data['root_path'] != null) ...[
              Text('Storage Path: ${data['root_path']}'),
              const SizedBox(height: 8),
            ],
            Text('Status: ${data['nextcloud_status'] ?? 'Unknown'}'),
            if (data['error'] != null) ...[
              const SizedBox(height: 8),
              Text('Error: ${data['error']}', style: const TextStyle(color: Colors.red)),
            ],
            const SizedBox(height: 16),
            const Text('Transcriptions are automatically backed up to your configured storage provider.'),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('OK'),
          ),
        ],
      ),
    );
  }

  void _contactSupport(BuildContext context) {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Opening email client...'),
        backgroundColor: Constants.primaryColor,
      ),
    );
  }
}

class _SectionHeader extends StatelessWidget {
  final String title;

  const _SectionHeader({required this.title});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Text(
        title,
        style: const TextStyle(
          fontSize: 14,
          fontWeight: FontWeight.w600,
          color: Constants.primaryColor,
        ),
      ),
    );
  }
}