import 'package:flutter_test/flutter_test.dart';
import 'package:flutter/material.dart';
import 'package:integration_test/integration_test.dart';
import 'package:mmt/main.dart' as app;

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  group('MMT Web App Tests', () {
    testWidgets('Login flow', (tester) async {
      app.main();
      await tester.pumpAndSettle();

      // Test guest login
      await tester.tap(find.text('Continue as Guest'));
      await tester.pumpAndSettle();

      expect(find.text('Transcription'), findsOneWidget);
    });

    testWidgets('File upload', (tester) async {
      app.main();
      await tester.pumpAndSettle();

      // Login first
      await tester.tap(find.text('Continue as Guest'));
      await tester.pumpAndSettle();

      // Test file picker
      await tester.tap(find.byIcon(Icons.upload_file));
      await tester.pumpAndSettle();
    });

    testWidgets('Audio recording', (tester) async {
      app.main();
      await tester.pumpAndSettle();

      await tester.tap(find.text('Continue as Guest'));
      await tester.pumpAndSettle();

      // Test record button
      await tester.tap(find.byIcon(Icons.mic));
      await tester.pumpAndSettle();

      expect(find.text('Recording...'), findsOneWidget);
    });
  });
}
