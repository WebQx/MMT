import 'dart:convert';
import 'package:http/http.dart' as http;
import '../utils/constants.dart';

class AuthService {
  Future<Map<String, dynamic>> loginWithKeycloak(String token) async {
    try {
      final response = await http.post(
        Uri.parse('${Constants.baseUrl}/login/oauth2'),
        headers: {
          'Content-Type': 'application/json',
        },
        body: jsonEncode({
          'token': token,
        }),
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Keycloak login failed: ${response.body}');
      }
    } catch (e) {
      throw Exception('Network error during Keycloak login: $e');
    }
  }

  Future<Map<String, dynamic>> loginAsGuest() async {
    try {
      final response = await http.post(
        Uri.parse('${Constants.baseUrl}/login/guest'),
        headers: {
          'Content-Type': 'application/json',
        },
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Guest login failed: ${response.body}');
      }
    } catch (e) {
      // If backend is unreachable and offline auth is allowed (dev only),
      // return a simple mock token so the UI can proceed for demo purposes.
      if (Constants.allowOfflineAuth) {
        return {
          'access_token': '${Constants.offlineGuestTokenPrefix}-${DateTime.now().millisecondsSinceEpoch}',
          'token_type': 'Bearer',
          'expires_in': 3600,
          'offline': true,
        };
      }

      throw Exception('Network error during guest login: $e');
    }
  }

  Future<Map<String, dynamic>> loginAsGuestWithLanguage(String language) async {
    try {
      final response = await http.post(
        Uri.parse('${Constants.baseUrl}/login/guest'),
        headers: {
          'Content-Type': 'application/json',
        },
        body: jsonEncode({'language': language}),
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Guest login failed: ${response.body}');
      }
    } catch (e) {
      if (Constants.allowOfflineAuth) {
        return {
          'access_token': '${Constants.offlineGuestTokenPrefix}-${DateTime.now().millisecondsSinceEpoch}',
          'token_type': 'Bearer',
          'expires_in': 3600,
          'language': language,
          'offline': true,
        };
      }

      throw Exception('Network error during guest login: $e');
    }
  }

  Future<Map<String, dynamic>> loginLocal(String email, String password, String language) async {
    try {
      final response = await http.post(
        Uri.parse('${Constants.baseUrl}/login/local'),
        headers: {
          'Content-Type': 'application/json',
        },
        body: jsonEncode({'email': email, 'password': password, 'language': language}),
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Local login failed: ${response.body}');
      }
    } catch (e) {
      if (Constants.allowOfflineAuth) {
        return {
          'access_token': '${Constants.offlineGuestTokenPrefix}-${DateTime.now().millisecondsSinceEpoch}',
          'token_type': 'Bearer',
          'expires_in': 3600,
          'language': language,
          'offline': true,
        };
      }

      throw Exception('Network error during local login: $e');
    }
  }

  Future<bool> validateToken(String token) async {
    try {
      final response = await http.get(
        Uri.parse('${Constants.baseUrl}/health'),
        headers: {
          'Authorization': 'Bearer $token',
        },
      );

      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }
}