// ignore_for_file: deprecated_member_use, unused_field, unused_element

import 'package:flutter_appauth/flutter_appauth.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:speech_to_text/speech_to_text.dart' as stt;
import 'package:permission_handler/permission_handler.dart';
import 'package:file_picker/file_picker.dart';

import 'package:flutter/material.dart';
import 'config/api_config.dart';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:printing/printing.dart';
import 'passkey_intro_page.dart';
import 'package:url_launcher/url_launcher.dart';
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

  Future<void> _loginAsGuest() async {
    final uri = Uri.parse('$BASE_URL/login/guest');
    setState(() {
      _result = 'Attempting guest login @ ${uri.toString()}';
    });
    http.Response response;
    try {
      response = await http.post(uri).timeout(const Duration(seconds: 15));
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
      title: 'MMT',
      home: Scaffold(
        backgroundColor: const Color(0xFFF5F6FA),
        body: Center(
          child: !_isLoggedIn
              ? SingleChildScrollView(
                  child: Center(
                    child: Card(
                      elevation: 8,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(16),
                      ),
                      child: Padding(
                        padding: const EdgeInsets.all(32.0),
                        child: Column(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            // Logo or App Name
                            Padding(
                              padding: const EdgeInsets.only(bottom: 24.0),
                              child: Column(
                                children: [
                                  // Replace with your logo if available
                                  Icon(Icons.health_and_safety,
                                      size: 48, color: Colors.blueAccent),
                                  const SizedBox(height: 8),
                                  Text('MMT Health',
                                      style: TextStyle(
                                          fontSize: 24,
                                          fontWeight: FontWeight.bold,
                                          color: Colors.blueAccent)),
                                ],
                              ),
                            ),
                            // Email Field
                            TextField(
                              decoration: InputDecoration(
                                labelText: 'Email',
                                border: OutlineInputBorder(
                                    borderRadius: BorderRadius.circular(8)),
                              ),
                            ),
                            const SizedBox(height: 16),
                            // Password Field
                            TextField(
                              obscureText: true,
                              decoration: InputDecoration(
                                labelText: 'Password',
                                border: OutlineInputBorder(
                                    borderRadius: BorderRadius.circular(8)),
                              ),
                            ),
                            const SizedBox(height: 24),
                            SizedBox(
                              width: double.infinity,
                              child: ElevatedButton(
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: Colors.blueAccent,
                                  shape: RoundedRectangleBorder(
                                      borderRadius: BorderRadius.circular(8)),
                                  padding:
                                      const EdgeInsets.symmetric(vertical: 16),
                                ),
                                onPressed: _loginWithKeycloak,
                                child: const Text('Sign In',
                                    style: TextStyle(fontSize: 16)),
                              ),
                            ),
                            const SizedBox(height: 16),
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                TextButton(
                                  onPressed: () {
                                    Navigator.of(context).push(
                                      MaterialPageRoute(
                                        builder: (context) =>
                                            PasskeyIntroPage(),
                                      ),
                                    );
                                  },
                                  child: const Text('Sign Up'),
                                ),
                                TextButton(
                                  onPressed:
                                      () {}, // TODO: Implement forgot password
                                  child: const Text('Forgot Password?'),
                                ),
                              ],
                            ),
                            const SizedBox(height: 16),
                            ElevatedButton(
                              onPressed: _loginAsGuest,
                              style: ElevatedButton.styleFrom(
                                backgroundColor: Colors.grey[300],
                                foregroundColor: Colors.black,
                                shape: RoundedRectangleBorder(
                                    borderRadius: BorderRadius.circular(8)),
                              ),
                              child: const Text('Continue as Guest'),
                            ),
                            if (_result.isNotEmpty) ...[
                              const SizedBox(height: 20),
                              Text(_result,
                                  style: const TextStyle(color: Colors.red)),
                            ],
                          ],
                        ),
                      ),
                    ),
                  ),
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
                                value: 'cellular',
                                child: Text('Cellular Data')),
                            DropdownMenuItem(
                                value: 'wifi', child: Text('WiFi')),
                            DropdownMenuItem(
                                value: 'cloud', child: Text('Cloud-Based')),
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
                    // Ambient mode toggle (only available in WiFi mode)
                    if (_selectedMode == 'wifi') ...[
                      Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Checkbox(
                            value: _ambientMode,
                            onChanged: (val) {
                              setState(() {
                                _ambientMode = val!;
                              });
                              if (val!) {
                                _startAmbientMode();
                              } else {
                                _stopAmbientMode();
                              }
                            },
                          ),
                          const Text('Enable Ambient Mode'),
                        ],
                      ),
                      if (_ambientMode)
                        Column(
                          children: [
                            _isListening
                                ? const Text('Listening...')
                                : const Text('Not listening'),
                            Text('Ambient Transcript: $_ambientText'),
                          ],
                        ),
                    ],
                    const SizedBox(height: 20),
                    if (_transcriptionType == 'realtime')
                      if (_phiConsent)
                        ElevatedButton(
                          onPressed: _isUploading
                              ? null
                              : () async {
                                  FilePickerResult? result = await FilePicker
                                      .platform
                                      .pickFiles(type: FileType.audio);
                                  if (result != null &&
                                      result.files.single.path != null) {
                                    final file =
                                        File(result.files.single.path!);
                                    await _uploadAndTranscribe(file);
                                  } else {
                                    setState(() {
                                      _result = 'No file selected.';
                                    });
                                  }
                                },
                          child: const Text('Upload & Transcribe'),
                        )
                      else ...[
                        ElevatedButton(
                          onPressed: _isUploading
                              ? null
                              : () async {
                                  FilePickerResult? result = await FilePicker
                                      .platform
                                      .pickFiles(type: FileType.audio);
                                  if (result != null &&
                                      result.files.single.path != null) {
                                    setState(() {
                                      _savedAudioPath =
                                          result.files.single.path;
                                      _result =
                                          'Audio recorded. You can transcribe it later.';
                                    });
                                  } else {
                                    setState(() {
                                      _result = 'No file selected.';
                                    });
                                  }
                                },
                          child: const Text('Record Now (Save for Later)'),
                        ),
                        if (_phiConsent && _savedAudioPath != null)
                          ElevatedButton(
                            onPressed: _isUploading
                                ? null
                                : () async {
                                    final file = File(_savedAudioPath!);
                                    await _uploadAndTranscribe(file);
                                  },
                            child: const Text('Transcribe Saved Audio'),
                          ),
                      ],
                    const SizedBox(height: 20),
                    _isUploading
                        ? const CircularProgressIndicator()
                        : Text(_result),
                    if (_result.isNotEmpty &&
                        !_isUploading &&
                        _transcriptionType == 'realtime' &&
                        _phiConsent) ...[
                      const SizedBox(height: 20),
                      ElevatedButton(
                        onPressed: () async {
                          await Printing.layoutPdf(
                            onLayout: (format) async =>
                                await Printing.convertHtml(
                              format: format,
                              html:
                                  '<h1>Transcription Result</h1><p>${_sanitizeForShare(_result).replaceAll("\n", "<br>")}</p>',
                            ),
                          );
                        },
                        child: const Text('Print Result'),
                      ),
                      const SizedBox(height: 10),
                      ElevatedButton(
                        onPressed: () async {
                          final subject =
                              Uri.encodeComponent('Transcription Result');
                          final body =
                              Uri.encodeComponent(_sanitizeForShare(_result));
                          final uri =
                              Uri.parse('mailto:?subject=$subject&body=$body');
                          if (await canLaunchUrl(uri)) {
                            await launchUrl(uri);
                          }
                        },
                        child: const Text('Email Result'),
                      ),
                    ],
                  ],
                ),
        ),
      ),
    );
  }
}
