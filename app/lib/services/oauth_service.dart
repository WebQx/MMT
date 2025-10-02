import 'dart:convert';
import 'package:http/http.dart' as http;
import '../utils/constants.dart';
import '../utils/oauth_redirect.dart';

class OAuthService {
  Future<Uri> getAuthorizeUrl(String provider) async {
    final resp = await http.get(Uri.parse('${Constants.baseUrl}/auth/oauth/$provider/authorize'));
    if (resp.statusCode != 200) {
      throw Exception('Failed to fetch authorize URL for $provider: ${resp.body}');
    }
    final data = jsonDecode(resp.body) as Map<String, dynamic>;
    final url = data['authorize_url'] as String?;
    if (url == null || url.isEmpty) {
      throw Exception('Provider $provider returned empty authorize_url');
    }
    return Uri.parse(url);
  }

  Future<void> beginOAuthFlow(String provider) async {
    final authUrl = await getAuthorizeUrl(provider);
    redirectToExternal(authUrl.toString());
  }
}
