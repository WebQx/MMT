import 'package:flutter_test/flutter_test.dart';
import 'package:mmt/main.dart' as app;

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('Guest login button & title render', (tester) async {
    app.main();
    await tester.pumpAndSettle();

    expect(find.text('MMT Transcription'), findsOneWidget);
    expect(find.text('Continue as Guest'), findsOneWidget);
  });
}
