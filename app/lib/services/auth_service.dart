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
      throw Exception('Network error during guest login: $e');
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