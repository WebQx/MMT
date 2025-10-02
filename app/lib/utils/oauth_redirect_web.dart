// Web implementation using window.location for redirect.
// ignore: avoid_web_libraries_in_flutter
import 'dart:html' as html;

void redirectToExternal(String url) {
  html.window.location.assign(url);
}
