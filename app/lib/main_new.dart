import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:sentry_flutter/sentry_flutter.dart';
import 'providers/app_state_provider.dart';
import 'screens/home_screen.dart';
import 'screens/login_screen.dart';
import 'screens/transcription_screen.dart';
import 'screens/settings_screen.dart';
import 'screens/openemr_screen.dart';
import 'theme/app_theme.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  final prefs = await SharedPreferences.getInstance();
  final sentryDsn = const String.fromEnvironment('SENTRY_DSN', defaultValue: '');
  
  if (sentryDsn.isNotEmpty) {
    SentryFlutter.init((o) {
      o.dsn = sentryDsn;
      o.tracesSampleRate = 0.2;
    }, appRunner: () => runApp(MyApp(prefs: prefs)));
  } else {
    runApp(MyApp(prefs: prefs));
  }
}

class MyApp extends StatelessWidget {
  final SharedPreferences prefs;
  
  const MyApp({super.key, required this.prefs});

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider(
      create: (context) => AppStateProvider(prefs),
      child: Consumer<AppStateProvider>(
        builder: (context, appState, _) {
          return MaterialApp(
            title: 'WebQx MMT - Medical Transcription',
            theme: AppTheme.lightTheme,
            darkTheme: AppTheme.darkTheme,
            themeMode: appState.themeMode,
            home: _buildHomeScreen(appState),
            routes: {
              '/login': (context) => const LoginScreen(),
              '/home': (context) => const HomeScreen(),
              '/transcription': (context) => const TranscriptionScreen(),
              '/settings': (context) => const SettingsScreen(),
              '/openemr': (context) => const OpenEMRScreen(),
            },
          );
        },
      ),
    );
  }
  
  Widget _buildHomeScreen(AppStateProvider appState) {
    if (!appState.isAuthenticated) {
      return const LoginScreen();
    }
    
    if (!appState.onboardingCompleted) {
      // You can add onboarding screen here if needed
      return const HomeScreen();
    }
    
    return const HomeScreen();
  }
}
