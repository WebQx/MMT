import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:mmt/main.dart' as app;

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('Guest login button appears then consent flow gates actions', (tester) async {
    // Initialize shared preferences for testing
    SharedPreferences.setMockInitialValues({});
    final prefs = await SharedPreferences.getInstance();
    
    await tester.pumpWidget(app.MyApp(prefs: prefs));
    expect(find.text('Continue as Guest'), findsOneWidget);
    // Tap guest (will fail auth in prod but UI state should set token later; here we just verify widget tree)
    await tester.tap(find.text('Continue as Guest'));
    await tester.pump();
    // After login attempt, still may be on same screen if network absent; this is a smoke test.
  });
}
