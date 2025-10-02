// Conditional export selecting platform implementation for external redirect.
export 'oauth_redirect_stub.dart' if (dart.library.html) 'oauth_redirect_web.dart';
