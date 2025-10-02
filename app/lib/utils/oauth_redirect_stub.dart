// Non-web stub: throws by default (can be extended for mobile deep link or custom tabs).
void redirectToExternal(String url) {
  throw UnsupportedError('OAuth web redirect not implemented for this platform: $url');
}
