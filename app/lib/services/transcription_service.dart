import 'dart:convert';
import 'dart:io';
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
}