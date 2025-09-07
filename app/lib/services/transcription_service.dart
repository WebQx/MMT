import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';
import 'package:http/http.dart' as http;
import '../utils/constants.dart';
import '../models/transcription_result.dart';

class TranscriptionService {
  Future<TranscriptionResult> transcribeLocal({
    required File audioFile,
    required String authToken,
    String language = 'auto',
    String? prompt,
  }) async {
    try {
      var request = http.MultipartRequest(
        'POST',
        Uri.parse('${Constants.baseUrl}/transcribe/'),
      );

      request.headers['Authorization'] = 'Bearer $authToken';
      request.fields['language'] = language;
      if (prompt != null) {
        request.fields['prompt'] = prompt;
      }

      request.files.add(await http.MultipartFile.fromPath(
        'file',
        audioFile.path,
      ));

      final response = await request.send();
      final responseBody = await response.stream.bytesToString();

      if (response.statusCode == 200) {
        final data = jsonDecode(responseBody);
        return TranscriptionResult.fromJson(data);
      } else {
        throw Exception('Local transcription failed: $responseBody');
      }
    } catch (e) {
      throw Exception('Network error during local transcription: $e');
    }
  }

  Future<TranscriptionResult> transcribeCloud({
    required File audioFile,
    required String authToken,
    String language = 'auto',
    String? prompt,
  }) async {
    try {
      var request = http.MultipartRequest(
        'POST',
        Uri.parse('${Constants.baseUrl}/transcribe/cloud/'),
      );

      request.headers['Authorization'] = 'Bearer $authToken';
      request.fields['language'] = language;
      if (prompt != null) {
        request.fields['prompt'] = prompt;
      }

      request.files.add(await http.MultipartFile.fromPath(
        'file',
        audioFile.path,
      ));

      final response = await request.send();
      final responseBody = await response.stream.bytesToString();

      if (response.statusCode == 200) {
        final data = jsonDecode(responseBody);
        return TranscriptionResult.fromJson(data);
      } else {
        throw Exception('Cloud transcription failed: $responseBody');
      }
    } catch (e) {
      throw Exception('Network error during cloud transcription: $e');
    }
  }

  Future<Map<String, dynamic>> uploadChunk({
    required File chunkFile,
    required String authToken,
    required int chunkNumber,
    required int totalChunks,
    required String fileId,
  }) async {
    try {
      var request = http.MultipartRequest(
        'POST',
        Uri.parse('${Constants.baseUrl}/upload_chunk/'),
      );

      request.headers['Authorization'] = 'Bearer $authToken';
      request.fields['chunk_number'] = chunkNumber.toString();
      request.fields['total_chunks'] = totalChunks.toString();
      request.fields['file_id'] = fileId;

      request.files.add(await http.MultipartFile.fromPath(
        'chunk',
        chunkFile.path,
      ));

      final response = await request.send();
      final responseBody = await response.stream.bytesToString();

      if (response.statusCode == 200) {
        return jsonDecode(responseBody);
      } else {
        throw Exception('Chunk upload failed: $responseBody');
      }
    } catch (e) {
      throw Exception('Network error during chunk upload: $e');
    }
  }

  Future<Map<String, dynamic>> getNetworkAdvice(String authToken) async {
    try {
      final response = await http.get(
        Uri.parse('${Constants.baseUrl}/network_advice/'),
        headers: {
          'Authorization': 'Bearer $authToken',
        },
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Network advice failed: ${response.body}');
      }
    } catch (e) {
      throw Exception('Network error during network advice: $e');
    }
  }

  Future<Map<String, dynamic>> parseChart({
    required String authToken,
    required String text,
    String templateKey = 'general_soap',
  }) async {
    try {
      final response = await http.post(
        Uri.parse('${Constants.baseUrl}/chart/parse'),
        headers: {
          'Authorization': 'Bearer $authToken',
          'Content-Type': 'application/json',
        },
        body: jsonEncode({'text': text, 'template_key': templateKey}),
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body) as Map<String, dynamic>;
      } else {
        throw Exception('Chart parse failed: ${response.body}');
      }
    } catch (e) {
      throw Exception('Network error during chart parse: $e');
    }
  }

  /// Web-friendly JSON upload using base64 audio for cloud transcription
  Future<TranscriptionResult> transcribeCloudJson({
    required Uint8List audioBytes,
    required String authToken,
    String language = 'auto',
    String? prompt,
  }) async {
    try {
      final body = {
        'audio_b64': base64Encode(audioBytes),
        'language': language,
      };
      if (prompt != null) body['prompt'] = prompt;

      final response = await http.post(
        Uri.parse('${Constants.baseUrl}/transcribe/cloud/'),
        headers: {
          'Authorization': 'Bearer $authToken',
          'Content-Type': 'application/json'
        },
        body: jsonEncode(body),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return TranscriptionResult.fromJson(data);
      } else {
        throw Exception('Cloud JSON transcription failed: ${response.body}');
      }
    } catch (e) {
      throw Exception('Network error during cloud JSON transcription: $e');
    }
  }
}
