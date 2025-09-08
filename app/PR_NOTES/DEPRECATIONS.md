DEPRECATIONS and recommended fixes
=================================

This file summarizes deprecations and analyzer notes found during the
`feat/ci-flutter` work and proposes minimal, safe, idiomatic replacements.

Summary (found by `flutter analyze` on 2025-09-07)
- Deprecated API: `listenMode` usage in `lib/main.dart` (speech_to_text)
- Deprecated API: `Printing.convertHtml` usage in `lib/main.dart` (printing)
- Deprecated Radio API usage (`groupValue` / `onChanged`) in several screens
- Deprecated `Color.withOpacity` usage in `_StatusItem` styling

Goals
- Replace deprecated APIs with recommended alternatives where safe.
- Keep changes minimal and well-tested: do one small API migration at a time.
- Prefer clarity over cleverness; if a migration touches many widgets, add
  targeted tests or a manual smoke test plan.

Recommended step-by-step plan
1) Speech `listenMode` migration (low-risk):
   - Current: `_speech!.listen(..., listenMode: stt.ListenMode.dictation)`
   - Recommendation: use the new `SpeechListenOptions` config object instead of
     the deprecated `listenMode` named parameter. Example (pseudocode):

       final opts = stt.SpeechListenOptions(listenMode: stt.ListenMode.dictation);
       _speech!.listen(onResult: ..., options: opts);

   - Rationale: aligns with `speech_to_text` recent API and avoids deprecation.

2) Printing API migration (medium-risk):
   - Current: `Printing.convertHtml(...)` (deprecated)
   - Recommendation: build a PDF using the `pdf` package (create a `pw.Document`)
     and pass its bytes into `Printing.layoutPdf` or use `Printing.convertHtml`
     wrapper utilities only if conversion isn't deprecated in your package version.
   - Notes: This migration is slightly more code but yields better control.

3) Radio group API (medium-risk):
   - Current: `RadioListTile` passing `groupValue` and `onChanged` at many places.
   - Recommendation: switch to `RadioGroup` ancestor widgets where available,
     or, if you must preserve current behavior, replace deprecated usage with
     the new appropriate API provided by your Flutter SDK (see migration guide).

4) Color.withOpacity (low-risk):
   - Current: `color.withOpacity(0.1)` used to tint status badges.
   - Recommendation: use `Color.alphaBlend` or construct a color with the
     desired alpha via `Color.fromARGB((0.1*255).round(), color.red, color.green, color.blue)`
     if you need to preserve exact semantics without deprecation warnings.

Proposed immediate follow-ups
- I can implement step (1) (speech `listenMode`) and step (4) (color alpha)
  as small, safe patches and push them to this branch. They are limited in
  scope and simple to validate with `flutter analyze` and a quick `flutter run`.
- Step (2) (Printing) and step (3) (RadioGroup) will need slightly larger
  edits and manual verification; I can prepare PR-ready patches for those next.

If you want me to proceed
- Reply with which steps to apply now. I recommend starting with: 1) Speech
  listenMode migration and 4) Color/opacity migration. I will then run
  `flutter analyze` and `flutter test` and push the changes to `feat/ci-flutter`.

Notes about safety and testing
- I'll keep changes minimal and run `flutter analyze` before committing.
- For UI-affecting changes (radio groups, printing), I will prepare small
  screenshots and test instructions so you can confirm behavior manually.

----
Generated automatically by the CI assist script on 2025-09-07.
