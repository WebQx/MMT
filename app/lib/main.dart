import 'package:flutter_appauth/flutter_appauth.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:speech_to_text/speech_to_text.dart' as stt;
import 'package:permission_handler/permission_handler.dart';
import 'package:file_picker/file_picker.dart';

import 'package:flutter/material.dart';
import 'config/api_config.dart';
import 'widgets/home_page.dart';
import 'widgets/login_card.dart';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:printing/printing.dart';
import 'passkey_intro_page.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:flutter/foundation.dart' show kIsWeb;
// Web-only import for reading window location fragment
// ignore: avoid_web_libraries_in_flutter
import 'dart:html' as html;
import 'package:sentry_flutter/sentry_flutter.dart';

void main() {
  final sentryDsn =
      const String.fromEnvironment('SENTRY_DSN', defaultValue: '');
  if (sentryDsn.isNotEmpty) {
    SentryFlutter.init((o) {
      o.dsn = sentryDsn;
      o.tracesSampleRate = 0.2;
    }, appRunner: () => runApp(const MyApp()));
  } else {
    runApp(const MyApp());
  }
}

class MyApp extends StatefulWidget {
  const MyApp({super.key});

  @override
  State<MyApp> createState() => _MyAppState();
}

class _MyAppState extends State<MyApp> {
  final FlutterAppAuth _appAuth = FlutterAppAuth();
  final FlutterSecureStorage _secureStorage = const FlutterSecureStorage();
  String? _accessToken;
  String? _refreshToken;
  bool _isLoggedIn = false;
  String _selectedLanguage = 'en';

  // Keycloak config (replace with your values)
  final String _clientId = 'mmt-app';
  final String _redirectUrl = 'com.example.mmt:/oauthredirect';
  final String _issuer = const String.fromEnvironment('KEYCLOAK_ISSUER',
      defaultValue: 'https://your-keycloak-domain/realms/your-realm');
  final List<String> _scopes = ['openid', 'profile', 'email'];

  Future<void> _loginWithKeycloak() async {
    try {
      final result = await _appAuth.authorizeAndExchangeCode(
        AuthorizationTokenRequest(
          _clientId,
          _redirectUrl,
          issuer: _issuer,
          scopes: _scopes,
        ),
      );
      if (result != null && result.accessToken != null) {
        setState(() {
          _accessToken = result.accessToken;
          _isLoggedIn = true;
        });
        await _secureStorage.write(key: 'access_token', value: _accessToken);
        if (result.refreshToken != null) {
          _refreshToken = result.refreshToken;
          await _secureStorage.write(
              key: 'refresh_token', value: _refreshToken);
        }
      }
    } catch (e) {
      setState(() {
        _result = 'Login failed: $e';
      });
    }
  }

  Future<void> _openProviderAuthorize(String provider) async {
    final uri = Uri.parse('$BASE_URL/auth/oauth/$provider/authorize');
    try {
      final resp = await http.get(uri).timeout(const Duration(seconds: 8));
      if (resp.statusCode == 200) {
        final data = json.decode(resp.body) as Map<String, dynamic>;
        final auth = data['authorize_url'] as String?;
        if (auth != null) {
          await launchUrl(Uri.parse(auth), mode: LaunchMode.externalApplication);
          // On web the provider flow should redirect back to frontend; parse fragment
          if (kIsWeb) {
            // small delay for redirect
            await Future.delayed(const Duration(seconds: 1));
            _maybeCaptureFragmentToken();
          }
          return;
        }
      }
      setState(() => _result = 'Failed to get authorize URL for $provider');
    } catch (e) {
      setState(() => _result = 'Network error opening provider authorize: $e');
    }
  }

  void _maybeCaptureFragmentToken() async {
    if (!kIsWeb) return;
    try {
      final frag = html.window.location.hash; // e.g. #access_token=...
      if (frag != null && frag.isNotEmpty) {
        final cleaned = frag.startsWith('#') ? frag.substring(1) : frag;
        final parts = Uri.splitQueryString(cleaned);
        final token = parts['access_token'];
        if (token != null) {
          setState(() {
            _accessToken = token;
            _isLoggedIn = true;
            _result = 'SSO login succeeded';
          });
          await _secureStorage.write(key: 'access_token', value: _accessToken);
          // Clear fragment for cleanliness
          html.window.history.replaceState(null, '', html.window.location.pathname);
        }
      }
    } catch (_) {}
  }

  Future<void> _loginAsGuest() async {
    final uri = Uri.parse('$BASE_URL/login/guest');
    setState(() {
      _result = 'Attempting guest login @ ${uri.toString()}';
    });
    http.Response response;
    try {
      response = await http.post(uri, headers: {'Content-Type': 'application/json'}, body: json.encode({'language': _selectedLanguage})).timeout(const Duration(seconds: 15));
    } catch (e) {
      setState(() {
        _result =
            'Guest login network error: $e\nCheck backend running & BASE_URL=$BASE_URL';
      });
      return;
    }
    if (response.statusCode == 200) {
      Map<String, dynamic> data = {};
      try {
        data = json.decode(response.body) as Map<String, dynamic>;
      } catch (_) {}
      final token = data['access_token'] as String?;
      if (token == null) {
        setState(() {
          _result = 'Guest login response missing access_token';
        });
        return;
      }
      setState(() {
        _accessToken = token;
        _isLoggedIn = true;
        _result = 'Guest login succeeded';
      });
      await _secureStorage.write(key: 'access_token', value: _accessToken);
    } else {
      setState(() {
        _result =
            'Guest login failed: HTTP ${response.statusCode} ${response.reasonPhrase}\nBody: ${response.body}\n(BASE_URL=$BASE_URL)';
      });
    }
  }

  Future<void> _loginWithLocal(String email, String password) async {
    final uri = Uri.parse('$BASE_URL/login/local');
    setState(() {
      _result = 'Attempting local login as $email';
      _isUploading = true;
    });
    http.Response response;
    try {
    response = await http
      .post(uri, headers: {'Content-Type': 'application/json'}, body: json.encode({'email': email, 'password': password, 'language': _selectedLanguage}))
          .timeout(const Duration(seconds: 15));
    } catch (e) {
      setState(() {
        _result = 'Local login network error: $e\nCheck backend & BASE_URL=$BASE_URL';
        _isUploading = false;
      });
      return;
    }
    setState(() {
      _isUploading = false;
    });
    if (response.statusCode == 200) {
      Map<String, dynamic> data = {};
      try {
        data = json.decode(response.body) as Map<String, dynamic>;
      } catch (_) {}
      final token = data['access_token'] as String?;
      if (token == null) {
        setState(() {
          _result = 'Local login response missing access_token';
        });
        return;
      }
      setState(() {
        _accessToken = token;
        _isLoggedIn = true;
        _result = 'Local login succeeded';
      });
      await _secureStorage.write(key: 'access_token', value: _accessToken);
    } else {
      setState(() {
        _result = 'Local login failed: HTTP ${response.statusCode} ${response.reasonPhrase}\nBody: ${response.body}';
      });
    }
  }

  Future<String?> _getToken() async {
    if (_accessToken != null) return _accessToken;
    return await _secureStorage.read(key: 'access_token');
  }

  Future<void> _maybeRefreshToken() async {
    if (_refreshToken == null) {
      _refreshToken = await _secureStorage.read(key: 'refresh_token');
    }
    if (_refreshToken == null) return;
    try {
      final result = await _appAuth.token(TokenRequest(
        _clientId,
        _redirectUrl,
        issuer: _issuer,
        refreshToken: _refreshToken,
        scopes: _scopes,
      ));
      if (result != null && result.accessToken != null) {
        _accessToken = result.accessToken;
        await _secureStorage.write(key: 'access_token', value: _accessToken);
        if (result.refreshToken != null) {
          _refreshToken = result.refreshToken;
          await _secureStorage.write(
              key: 'refresh_token', value: _refreshToken);
        }
      }
    } catch (_) {}
  }

  Future<void> _showSignUpDialog() async {
    String email = '';
    String password = '';
    await showDialog(
      context: context,
      builder: (ctx) {
        return AlertDialog(
          title: const Text('Create account'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(onChanged: (v) => email = v, decoration: const InputDecoration(labelText: 'Email')),
              TextField(onChanged: (v) => password = v, decoration: const InputDecoration(labelText: 'Password'), obscureText: true),
            ],
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancel')),
            ElevatedButton(
                onPressed: () async {
                  Navigator.pop(ctx);
                },
                child: const Text('Create')),
          ],
        );
      },
    );
    if (email.isEmpty || password.isEmpty) return;
    setState(() {
      _isUploading = true;
      _result = 'Creating account...';
    });
    try {
      final uri = Uri.parse('$BASE_URL/register');
      final resp = await http.post(uri, headers: {'Content-Type': 'application/json'}, body: json.encode({'email': email, 'password': password, 'language': _selectedLanguage})).timeout(const Duration(seconds: 10));
      if (resp.statusCode == 200) {
        final data = json.decode(resp.body) as Map<String, dynamic>;
        final token = data['access_token'] as String?;
        if (token != null) {
          await _secureStorage.write(key: 'access_token', value: token);
          setState(() {
            _accessToken = token;
            _isLoggedIn = true;
            _result = 'Account created & logged in';
          });
        } else {
          setState(() => _result = 'Registration succeeded but no token returned');
        }
      } else {
        setState(() => _result = 'Registration failed: ${resp.statusCode} ${resp.body}');
      }
    } catch (e) {
      setState(() => _result = 'Registration network error: $e');
    } finally {
      setState(() => _isUploading = false);
    }
  }

  Future<http.Response> _retryingPost(Uri uri,
      {Map<String, String>? headers, Object? body, int retries = 2}) async {
    int attempt = 0;
    Duration backoff = const Duration(milliseconds: 400);
    while (true) {
      try {
        final resp = await http
            .post(uri, headers: headers, body: body)
            .timeout(const Duration(seconds: 30));
        if (resp.statusCode == 401 && attempt == 0) {
          // try refresh once
          await _maybeRefreshToken();
          attempt++;
          continue;
        }
        if (resp.statusCode >= 500 && attempt < retries) {
          await Future.delayed(backoff);
          backoff *= 2;
          attempt++;
          continue;
        }
        return resp;
      } catch (_) {
        if (attempt >= retries) rethrow;
        attempt++;
        await Future.delayed(backoff);
        backoff *= 2;
      }
    }
  }

  bool _ambientMode = false;
  bool _phiConsent = false;
  bool _isListening = false;
  stt.SpeechToText? _speech;
  String _ambientText = '';
  @override
  void initState() {
    super.initState();
    _speech = stt.SpeechToText();
  }

  bool _showHome = true;

  Future<void> _startAmbientMode() async {
    var status = await Permission.microphone.request();
    if (status.isGranted) {
      bool available = await _speech!.initialize(
        onStatus: (val) {
          if (val == 'done') {
            setState(() {
              _isListening = false;
            });
          }
        },
        onError: (val) {
          setState(() {
            _isListening = false;
          });
        },
      );
      if (available) {
        setState(() {
          _isListening = true;
          _ambientText = '';
        });
        _speech!.listen(
          onResult: (val) async {
            setState(() {
              _ambientText = val.recognizedWords;
            });
            if (val.finalResult && val.recognizedWords.isNotEmpty) {
              // Send to backend as text
              await _sendAmbientTranscript(val.recognizedWords);
            }
          },
          listenMode: stt.ListenMode.dictation,
        );
      }
    }
  }

  Future<void> _sendAmbientTranscript(String text) async {
    setState(() {
      _isUploading = true;
    });
    final uri = Uri.parse('$BASE_URL/transcribe/');
    final token = await _getToken();
    final response = await _retryingPost(
      uri,
      headers: {
        'Content-Type': 'application/json',
        if (token != null) 'Authorization': 'Bearer $token'
      },
      body: json.encode({'text': text, 'mode': 'ambient'}),
    );
    if (response.statusCode == 200) {
      setState(() {
        _result = 'Ambient transcript sent: $text';
      });
    } else {
      setState(() {
        _result = 'Error sending ambient transcript: ${response.body}';
      });
      await Sentry.captureMessage('Ambient send failed ${response.statusCode}');
    }
    setState(() {
      _isUploading = false;
    });
  }

  void _stopAmbientMode() {
    _speech?.stop();
    setState(() {
      _isListening = false;
    });
  }

  String? _savedAudioPath; // For record now, transcribe later
  // Add login step state
  int _loginStep = 0; // 0 = choose action, 1 = main UI
  String _transcriptionType = 'realtime'; // 'realtime' or 'record_later'
  String _result = '';
  bool _isUploading = false;
  String _selectedMode = 'wifi'; // Default mode
  double _bandwidth = 0;

  String _sanitizeForShare(String input) {
    // Placeholder PHI redaction: mask sequences of digits >4 and email-like patterns
    final digitRe = RegExp(r'\b\d{5,}\b');
    final emailRe = RegExp(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+');
    return input
        .replaceAllMapped(digitRe, (_) => '***')
        .replaceAllMapped(emailRe, (_) => '***');
  }

  // Optionally, you can still use bandwidth check for auto mode
  Future<void> _checkBandwidthAndSetMode() async {
    // Simulate bandwidth check (replace with real check if needed)
    _bandwidth = 1000;
    final response = await http
        .get(Uri.parse('$BASE_URL/network_advice/?bandwidth_kbps=$_bandwidth'));
    if (response.statusCode == 200) {
      final mode = json.decode(response.body)['mode'];
      setState(() {
        _selectedMode = mode == 'real_time' ? 'wifi' : 'cellular';
      });
    }
  }

  Future<void> _uploadAndTranscribe(File file) async {
    setState(() {
      _isUploading = true;
      _result = 'Uploading...';
    });
    String endpoint = '/transcribe/';
    Map<String, String> fields = {};
    if (_selectedMode == 'cellular') {
      endpoint = '/transcribe/';
      fields['real_time'] = 'false';
      fields['mode'] = 'cellular';
    } else if (_selectedMode == 'wifi') {
      endpoint = '/transcribe/';
      fields['real_time'] = 'true';
      fields['mode'] = 'wifi';
    } else if (_selectedMode == 'cloud') {
      endpoint = '/transcribe/?use_cloud=true';
      fields['mode'] = 'cloud';
    }
    final uri = Uri.parse('$BASE_URL$endpoint');
    final token = await _getToken();
    final request = http.MultipartRequest('POST', uri)
      ..files.add(await http.MultipartFile.fromPath('file', file.path))
      ..fields.addAll(fields);
    if (token != null) {
      request.headers['Authorization'] = 'Bearer $token';
    }
    final streamedResponse = await request.send();
    if (_selectedMode == 'wifi') {
      // Real-time: stream response
      final response =
          await streamedResponse.stream.transform(utf8.decoder).join();
      setState(() {
        _result = response;
        _isUploading = false;
      });
    } else {
      final response = await http.Response.fromStream(streamedResponse);
      if (response.statusCode == 200) {
        setState(() {
          _result = json.decode(response.body)['text'] ?? response.body;
        });
      } else {
        setState(() {
          _result = 'Error: ${response.body}';
        });
        await Sentry.captureMessage('Upload failed ${response.statusCode}');
      }
      setState(() {
        _isUploading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'WebQx Multilingual Medical Transcription (MMT)',
      home: Scaffold(
        backgroundColor: const Color(0xFFF5F6FA),
        body: _showHome
            ? HomePage(
                onGetStarted: () => setState(() => _showHome = false),
                onLearnMore: null,
              )
            : (!_isLoggedIn
        ? LoginCard(
                    onKeycloak: _loginWithKeycloak,
                    onGoogle: () => _openProviderAuthorize('google'),
                    onMicrosoft: () => _openProviderAuthorize('microsoft'),
                    onApple: () => _openProviderAuthorize('apple'),
                    onGuest: _loginAsGuest,
                    onLocalLogin: _loginWithLocal,
          onBack: () => setState(() => _showHome = true),
          onSignUp: _showSignUpDialog,
          onLanguageChanged: (lang) => setState(() => _selectedLanguage = lang),
                    resultText: _result,
                    isLoading: _isUploading,
                  )
            : Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  // ...existing code for main UI (transcription type, mode, etc.)...
                  Text('API Endpoint: $BASE_URL'),
                  const SizedBox(height: 20),
                  // Mode selection UI
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Text('Mode: '),
                      DropdownButton<String>(
                        value: _selectedMode,
                        items: const [
                          DropdownMenuItem(
                              value: 'cellular', child: Text('Cellular Data')),
                          DropdownMenuItem(value: 'wifi', child: Text('WiFi')),
                          DropdownMenuItem(value: 'cloud', child: Text('Cloud-Based')),
                        ],
                        onChanged: _isUploading
                            ? null
                            : (value) {
                                setState(() {
                                  _selectedMode = value!;
                                });
                              },
                      ),
                    ],
                  ),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Checkbox(
                        value: _phiConsent,
                        onChanged: (v) {
                          setState(() => _phiConsent = v ?? false);
                        },
                      ),
                      const SizedBox(width: 4),
                      const Expanded(
                          child: Text(
                              'I understand transcripts may contain sensitive (PHI) data.')),
                    ],
                  ),
                  // The rest of the main UI remains unchanged (upload/transcribe, ambient mode, etc.)
                ],
              ),
      ),
    );
  }
}
