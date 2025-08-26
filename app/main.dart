import 'package:flutter/material.dart';
import 'lib/config/api_config.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'MMT',
      home: Scaffold(
        appBar: AppBar(title: const Text('MMT Transcription')),
        body: Center(
          child: Text('API Endpoint: $BASE_URL'),
        ),
      ),
    );
  }
}
