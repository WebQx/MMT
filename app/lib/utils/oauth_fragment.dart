// Conditional export for web vs non-web implementation.
export 'oauth_fragment_stub.dart' if (dart.library.html) 'oauth_fragment_web.dart';
