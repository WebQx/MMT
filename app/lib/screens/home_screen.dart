// ignore_for_file: deprecated_member_use
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/app_state_provider.dart';
import '../utils/constants.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('MMT - Medical Transcription'),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: () => _logout(context),
          ),
        ],
      ),
      body: Consumer<AppStateProvider>(
        builder: (context, appState, _) {
          return SingleChildScrollView(
            padding: const EdgeInsets.all(Constants.padding),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Welcome Card
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(Constants.padding),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Icon(
                              appState.userType == 'guest'
                                  ? Icons.person
                                  : Icons.verified_user,
                              color: Constants.primaryColor,
                            ),
                            const SizedBox(width: 8),
                            Text(
                              'Welcome ${appState.userType == 'guest' ? 'Guest User' : 'User'}!',
                              style: const TextStyle(
                                fontSize: 20,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 8),
                        const Text(
                          'Healthcare-grade multilingual transcription platform',
                          style: TextStyle(color: Colors.grey),
                        ),
                      ],
                    ),
                  ),
                ),

                const SizedBox(height: 24),

                // Quick Actions
                const Text(
                  'Quick Actions',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 16),

                Row(
                  children: [
                    Expanded(
                      child: _QuickActionCard(
                        icon: Icons.mic,
                        title: 'Start Recording',
                        subtitle: 'Record audio for transcription',
                        color: Constants.primaryColor,
                        onTap: () => _navigateToTranscription(context),
                      ),
                    ),
                    const SizedBox(width: 16),
                    Expanded(
                      child: _QuickActionCard(
                        icon: Icons.upload_file,
                        title: 'Upload File',
                        subtitle: 'Select audio file',
                        color: Constants.secondaryColor,
                        onTap: () => _navigateToTranscription(context),
                      ),
                    ),
                  ],
                ),

                const SizedBox(height: 24),

                // Transcription Settings
                const Text(
                  'Transcription Settings',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 16),

                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(Constants.padding),
                    child: Column(
                      children: [
                        _SettingsTile(
                          title: 'Transcription Type',
                          subtitle: appState.selectedTranscriptionType,
                          icon: Icons.settings_voice,
                          onTap: () => _showTranscriptionTypeDialog(context),
                        ),
                        const Divider(),
                        _SettingsTile(
                          title: 'Network Mode',
                          subtitle: appState.selectedNetworkMode,
                          icon: Icons.network_check,
                          onTap: () => _showNetworkModeDialog(context),
                        ),
                        const Divider(),
                        _SettingsTile(
                          title: 'Language',
                          subtitle: appState.selectedLanguage == 'auto'
                              ? 'Auto-detect'
                              : appState.selectedLanguage,
                          icon: Icons.language,
                          onTap: () => _showLanguageDialog(context),
                        ),
                      ],
                    ),
                  ),
                ),

                const SizedBox(height: 24),

                // Status Card
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(Constants.padding),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'System Status',
                          style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        const SizedBox(height: 12),
                        _StatusItem(
                          label: 'API Connection',
                          status: 'Connected',
                          color: Constants.successColor,
                        ),
                        _StatusItem(
                          label: 'OpenAI Whisper',
                          status: 'Available',
                          color: Constants.successColor,
                        ),
                        _StatusItem(
                          label: 'Local Whisper',
                          status: 'Available',
                          color: Constants.successColor,
                        ),
                        _StatusItem(
                          label: 'OpenEMR Integration',
                          status: 'Configured',
                          color: Constants.successColor,
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          );
        },
      ),
    );
  }

  void _logout(BuildContext context) {
    final appState = Provider.of<AppStateProvider>(context, listen: false);
    appState.logout();
    Navigator.of(context).pushReplacementNamed('/login');
  }

  void _navigateToTranscription(BuildContext context) {
    Navigator.of(context).pushNamed('/transcription');
  }

  void _showTranscriptionTypeDialog(BuildContext context) {
    final appState = Provider.of<AppStateProvider>(context, listen: false);

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Select Transcription Type'),
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
        title: const Text('Select Network Mode'),
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

  void _showLanguageDialog(BuildContext context) {
    final appState = Provider.of<AppStateProvider>(context, listen: false);
    final languages = [
      'auto',
      'en',
      'es',
      'fr',
      'de',
      'ar',
      'zh',
      'ja',
      'ko',
      'hi',
      'pt'
    ];

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Select Language'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
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
    );
  }
}

class _QuickActionCard extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;
  final Color color;
  final VoidCallback onTap;

  const _QuickActionCard({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.color,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(Constants.borderRadius),
        child: Padding(
          padding: const EdgeInsets.all(Constants.padding),
          child: Column(
            children: [
              Icon(
                icon,
                size: 48,
                color: color,
              ),
              const SizedBox(height: 12),
              Text(
                title,
                style: const TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 4),
              Text(
                subtitle,
                style: const TextStyle(
                  fontSize: 12,
                  color: Colors.grey,
                ),
                textAlign: TextAlign.center,
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _SettingsTile extends StatelessWidget {
  final String title;
  final String subtitle;
  final IconData icon;
  final VoidCallback onTap;

  const _SettingsTile({
    required this.title,
    required this.subtitle,
    required this.icon,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return ListTile(
      leading: Icon(icon),
      title: Text(title),
      subtitle: Text(subtitle),
      trailing: const Icon(Icons.chevron_right),
      onTap: onTap,
    );
  }
}

class _StatusItem extends StatelessWidget {
  final String label;
  final String status;
  final Color color;

  const _StatusItem({
    required this.label,
    required this.status,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
            decoration: BoxDecoration(
              color: color.withOpacity(0.1),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Text(
              status,
              style: TextStyle(
                color: color,
                fontSize: 12,
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
