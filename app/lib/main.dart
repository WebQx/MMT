import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'services/auth_service.dart';
import 'services/transcription_service.dart';
import 'services/audio_service.dart';
import 'screens/login_screen.dart';
import 'screens/home_screen.dart';
import 'screens/transcription_screen.dart';
import 'screens/settings_screen.dart';
import 'theme/app_theme.dart';
import 'providers/app_state_provider.dart';
import 'utils/constants.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Initialize shared preferences
  final prefs = await SharedPreferences.getInstance();
  
  runApp(MMTApp(prefs: prefs));
}

class MMTApp extends StatelessWidget {
  final SharedPreferences prefs;
  
  const MMTApp({Key? key, required this.prefs}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(
          create: (_) => AppStateProvider(prefs),
        ),
        Provider<AuthService>(
          create: (_) => AuthService(),
        ),
        Provider<TranscriptionService>(
          create: (_) => TranscriptionService(),
        ),
        Provider<AudioService>(
          create: (_) => AudioService(),
        ),
      ],
      child: Consumer<AppStateProvider>(
        builder: (context, appState, _) {
          return MaterialApp(
            title: 'MMT - Medical Transcription',
            theme: AppTheme.lightTheme,
            darkTheme: AppTheme.darkTheme,
            themeMode: appState.themeMode,
            locale: appState.currentLocale,
            localizationsDelegates: const [
              GlobalMaterialLocalizations.delegate,
              GlobalWidgetsLocalizations.delegate,
              GlobalCupertinoLocalizations.delegate,
            ],
            supportedLocales: Constants.supportedLocales,
            debugShowCheckedModeBanner: false,
            home: appState.isAuthenticated 
              ? const MainNavigator()
              : const LoginScreen(),
            routes: {
              '/login': (context) => const LoginScreen(),
              '/home': (context) => const MainNavigator(),
              '/transcription': (context) => const TranscriptionScreen(),
              '/settings': (context) => const SettingsScreen(),
            },
          );
        },
      ),
    );
  }
}

class MainNavigator extends StatefulWidget {
  const MainNavigator({Key? key}) : super(key: key);

  @override
  State<MainNavigator> createState() => _MainNavigatorState();
}

class _MainNavigatorState extends State<MainNavigator> {
  int _currentIndex = 0;
  
  final List<Widget> _screens = [
    const HomeScreen(),
    const TranscriptionScreen(),
    const SettingsScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(
        index: _currentIndex,
        children: _screens,
      ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _currentIndex,
        onTap: (index) {
          setState(() {
            _currentIndex = index;
          });
        },
        type: BottomNavigationBarType.fixed,
        items: const [
          BottomNavigationBarItem(
            icon: Icon(Icons.home),
            label: 'Home',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.mic),
            label: 'Transcribe',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.settings),
            label: 'Settings',
          ),
        ],
      ),
    );
  }
}