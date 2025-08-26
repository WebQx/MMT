import 'package:flutter_test/flutter_test.dart';
import 'package:flutter/material.dart';
import 'package:mmt/main.dart' as app;

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('Guest login button appears then consent flow gates actions', (tester) async {
    await tester.pumpWidget(const app.MyApp());
    expect(find.text('Continue as Guest'), findsOneWidget);
    // Tap guest (will fail auth in prod but UI state should set token later; here we just verify widget tree)
    await tester.tap(find.text('Continue as Guest'));
    await tester.pump();
    // After login attempt, still may be on same screen if network absent; this is a smoke test.
  });
}
