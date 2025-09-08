import 'package:flutter_test/flutter_test.dart';
import 'package:flutter/material.dart';
import 'package:mmt/webqx_encounter_page.dart';

void main() {
  testWidgets('MiddlePanel shows Finalize Note button', (
    WidgetTester tester,
  ) async {
    await tester.pumpWidget(MaterialApp(home: Scaffold(body: MiddlePanel())));
    await tester.pumpAndSettle();

    final finalizeButton = find.text('Finalize Note');
    expect(finalizeButton, findsOneWidget);
  });
}
