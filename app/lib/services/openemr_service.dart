import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/patient.dart';
import '../models/encounter.dart';
import '../utils/constants.dart';
import '../services/auth_service.dart';

class OpenEMRService {
  final AuthService _authService = AuthService();

  Future<Map<String, String>> _getHeaders() async {
    final token = await _authService.getAccessToken();
    return {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer $token',
    };
  }

  /// Check if we have a valid connection to OpenEMR
  Future<bool> checkConnection() async {
    try {
      final headers = await _getHeaders();
      final response = await http.get(
        Uri.parse('${Constants.baseUrl}/fhir/Patient?_count=1'),
        headers: headers,
      ).timeout(const Duration(seconds: 10));
      
      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }

  /// Get SMART-on-FHIR authorize URL
  Future<String?> getAuthorizeUrl() async {
    try {
      final headers = await _getHeaders();
      final response = await http.get(
        Uri.parse('${Constants.baseUrl}/auth/fhir/authorize'),
        headers: headers,
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body) as Map<String, dynamic>;
        return data['authorize_url'] as String?;
      }
      return null;
    } catch (e) {
      throw Exception('Failed to get authorize URL: $e');
    }
  }

  /// Search for patients by name or ID
  Future<List<Patient>> searchPatients(String query) async {
    try {
      final headers = await _getHeaders();
      final encodedQuery = Uri.encodeComponent(query);
      final response = await http.get(
        Uri.parse('${Constants.baseUrl}/fhir/Patient?name=$encodedQuery&_count=20'),
        headers: headers,
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body) as Map<String, dynamic>;
        final bundle = data['entry'] as List<dynamic>? ?? [];
        
        return bundle.map((entry) {
          final resource = entry['resource'] as Map<String, dynamic>;
          return Patient.fromFhir(resource);
        }).toList();
      } else if (response.statusCode == 401) {
        throw Exception('Not authorized - please reconnect to OpenEMR');
      } else {
        throw Exception('Failed to search patients: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Failed to search patients: $e');
    }
  }

  /// Get a specific patient by ID
  Future<Patient?> getPatient(String patientId) async {
    try {
      final headers = await _getHeaders();
      final response = await http.get(
        Uri.parse('${Constants.baseUrl}/fhir/patient/$patientId'),
        headers: headers,
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body) as Map<String, dynamic>;
        return Patient.fromFhir(data);
      } else if (response.statusCode == 404) {
        return null;
      } else {
        throw Exception('Failed to get patient: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Failed to get patient: $e');
    }
  }

  /// Get encounters for a patient
  Future<List<Encounter>> getPatientEncounters(String patientId) async {
    try {
      final headers = await _getHeaders();
      final response = await http.get(
        Uri.parse('${Constants.baseUrl}/fhir/Encounter?patient=$patientId&_count=50&_sort=-date'),
        headers: headers,
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body) as Map<String, dynamic>;
        final bundle = data['entry'] as List<dynamic>? ?? [];
        
        return bundle.map((entry) {
          final resource = entry['resource'] as Map<String, dynamic>;
          return Encounter.fromFhir(resource);
        }).toList();
      } else {
        throw Exception('Failed to get encounters: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Failed to get encounters: $e');
    }
  }

  /// Create a new encounter for a patient
  Future<Encounter?> createEncounter(String patientId) async {
    try {
      final headers = await _getHeaders();
      final encounterData = {
        'resourceType': 'Encounter',
        'status': 'in-progress',
        'class': {
          'system': 'http://terminology.hl7.org/CodeSystem/v3-ActCode',
          'code': 'AMB',
          'display': 'ambulatory'
        },
        'type': [
          {
            'coding': [
              {
                'system': 'http://snomed.info/sct',
                'code': '185349003',
                'display': 'Encounter for check up'
              }
            ]
          }
        ],
        'subject': {
          'reference': 'Patient/$patientId'
        },
        'period': {
          'start': DateTime.now().toIso8601String()
        }
      };

      final response = await http.post(
        Uri.parse('${Constants.baseUrl}/fhir/Encounter'),
        headers: headers,
        body: json.encode(encounterData),
      );

      if (response.statusCode == 201) {
        final data = json.decode(response.body) as Map<String, dynamic>;
        return Encounter.fromFhir(data);
      } else {
        throw Exception('Failed to create encounter: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Failed to create encounter: $e');
    }
  }

  /// Send transcription as DocumentReference to OpenEMR
  Future<bool> createDocumentReference({
    required String patientId,
    required String? encounterId,
    required String transcriptionText,
    required String filename,
  }) async {
    try {
      final headers = await _getHeaders();
      final documentData = {
        'resourceType': 'DocumentReference',
        'status': 'current',
        'type': {
          'coding': [
            {
              'system': 'http://loinc.org',
              'code': '11488-4',
              'display': 'Consult note'
            }
          ]
        },
        'subject': {
          'reference': 'Patient/$patientId'
        },
        'content': [
          {
            'attachment': {
              'contentType': 'text/plain',
              'data': base64Encode(utf8.encode(transcriptionText)),
              'title': filename,
            }
          }
        ]
      };

      if (encounterId != null) {
        documentData['context'] = {
          'encounter': [
            {'reference': 'Encounter/$encounterId'}
          ]
        };
      }

      final response = await http.post(
        Uri.parse('${Constants.baseUrl}/fhir/DocumentReference'),
        headers: headers,
        body: json.encode(documentData),
      );

      return response.statusCode == 201;
    } catch (e) {
      throw Exception('Failed to create document reference: $e');
    }
  }

  /// Get document references for a patient
  Future<List<Map<String, dynamic>>> getPatientDocuments(String patientId) async {
    try {
      final headers = await _getHeaders();
      final response = await http.get(
        Uri.parse('${Constants.baseUrl}/fhir/DocumentReference?patient=$patientId&_count=50&_sort=-date'),
        headers: headers,
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body) as Map<String, dynamic>;
        final bundle = data['entry'] as List<dynamic>? ?? [];
        
        return bundle.map((entry) => entry['resource'] as Map<String, dynamic>).toList();
      } else {
        throw Exception('Failed to get documents: ${response.statusCode}');
      }
    } catch (e) {
      throw Exception('Failed to get documents: $e');
    }
  }
}
