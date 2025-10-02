// Web implementation using dart:html (only included in web builds).
// Extracts access_token from location.hash and then clears the fragment.
// Returns the token or null if not present.

// ignore: avoid_web_libraries_in_flutter
import 'dart:html' as html;

String? extractAccessTokenFromFragmentAndClean() {
  final loc = html.window.location;
  final hash = loc.hash; // includes leading '#'
  if (hash.isEmpty || !hash.contains('access_token=')) return null;
  final frag = hash.substring(1);
  String? token;
  for (final part in frag.split('&')) {
    final kv = part.split('=');
    if (kv.length == 2 && kv[0] == 'access_token') {
      token = Uri.decodeComponent(kv[1]);
      break;
    }
  }
  try { html.window.history.replaceState(null, '', loc.pathname ?? '/'); } catch (_) {}
  return token;
}
