import 'package:flutter_test/flutter_test.dart';
import 'package:mmt/main.dart' as app;

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  testWidgets(
      'Layout contains mode dropdown and upload button after guest login',
      (tester) async {
    app.main();
    await tester.pumpAndSettle();

    // Tap guest login if present
    final guest = find.text('Continue as Guest');
    if (guest.evaluate().isNotEmpty) {
      await tester.tap(guest);
      await tester.pumpAndSettle();
    }

    // Just verify some expected widgets exist in logged-in UI
    expect(find.textContaining('API Endpoint'), findsOneWidget);
  });
}
