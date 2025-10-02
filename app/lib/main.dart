import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'utils/oauth_fragment.dart';
import 'package:sentry_flutter/sentry_flutter.dart';
import 'providers/app_state_provider.dart';
import 'screens/home_screen.dart';
import 'screens/login_screen.dart';
import 'screens/transcription_screen.dart';
import 'screens/settings_screen.dart';
import 'screens/openemr_screen.dart';
import 'theme/app_theme.dart';
import 'widgets/demo_mode_banner.dart';
import 'utils/constants.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  // Extract token from URL fragment for web OAuth redirects (safe no-op off web).
  final fragmentToken = extractAccessTokenFromFragmentAndClean();

  final prefs = await SharedPreferences.getInstance();
  final sentryDsn = const String.fromEnvironment('SENTRY_DSN', defaultValue: '');
  if (fragmentToken != null && fragmentToken.isNotEmpty) {
    // Persist token and mark user authenticated optimistically. User type 'oauth'.
    await prefs.setString(Constants.authTokenKey, fragmentToken);
    await prefs.setString(Constants.userTypeKey, 'oauth');
  }
  
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
          // Show loading screen while provider is initializing
          if (!appState.isInitialized) {
            return MaterialApp(
              title: 'WebQx MMT - Medical Transcription',
              theme: AppTheme.lightTheme,
              darkTheme: AppTheme.darkTheme,
              themeMode: ThemeMode.system,
              home: const Scaffold(
                body: Center(
                  child: CircularProgressIndicator(),
                ),
              ),
            );
          }
          
          return MaterialApp(
            title: 'WebQx MMT - Medical Transcription',
            theme: AppTheme.lightTheme,
            darkTheme: AppTheme.darkTheme,
            themeMode: appState.themeMode,
            home: _wrapWithDemoBanner(_buildHomeScreen(appState)),
            routes: {
              '/login': (context) => const LoginScreen(),
              '/home': (context) => const HomeScreen(),
              '/transcription': (context) => const TranscriptionScreen(),
              '/settings': (context) => const SettingsScreen(),
              '/openemr': (context) => const OpenEMRScreen(),
            },
            onGenerateRoute: (settings) {
              // Ensure all routes have access to the Provider
              switch (settings.name) {
                case '/login':
                  return MaterialPageRoute(builder: (context) => const LoginScreen());
                case '/home':
                  return MaterialPageRoute(builder: (context) => const HomeScreen());
                case '/transcription':
                  return MaterialPageRoute(builder: (context) => const TranscriptionScreen());
                case '/settings':
                  return MaterialPageRoute(builder: (context) => const SettingsScreen());
                case '/openemr':
                  return MaterialPageRoute(builder: (context) => const OpenEMRScreen());
                default:
                  return null;
              }
            },
          );
        },
      ),
    );
  }

  Widget _wrapWithDemoBanner(Widget child) {
    // Heuristic: if BASE_URL still localhost or contains 'demo', show banner.
    final url = Constants.baseUrl;
    final isDemo = url.contains('localhost') || url.contains('demo');
    if (!isDemo) return child;
    return Scaffold(
      appBar: const DemoModeBanner(demoMode: true),
      body: child,
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