import 'dart:io';
import 'package:record/record.dart';
import 'package:audioplayers/audioplayers.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:path/path.dart' as path;
import '../utils/constants.dart';

class AudioService {
  final Record _recorder = Record();
  final AudioPlayer _player = AudioPlayer();
  
  bool _isRecording = false;
  bool _isPlaying = false;
  String? _currentRecordingPath;
  
  // Getters
  bool get isRecording => _isRecording;
  bool get isPlaying => _isPlaying;
  String? get currentRecordingPath => _currentRecordingPath;

  Future<bool> requestPermissions() async {
    final microphoneStatus = await Permission.microphone.request();
    return microphoneStatus == PermissionStatus.granted;
  }

  Future<void> startRecording({String? outputPath}) async {
    if (_isRecording) return;

    final hasPermission = await requestPermissions();
    if (!hasPermission) {
      throw Exception(Constants.micPermissionErrorMessage);
    }

    try {
      // Generate output path if not provided
      outputPath ??= await _generateRecordingPath();
      
      await _recorder.start(
        path: outputPath,
        encoder: AudioEncoder.wav,
        bitRate: 128000,
        samplingRate: 44100,
      );
      
      _isRecording = true;
      _currentRecordingPath = outputPath;
    } catch (e) {
      throw Exception('Failed to start recording: $e');
    }
  }

  Future<String?> stopRecording() async {
    if (!_isRecording) return null;

    try {
      final recordingPath = await _recorder.stop();
      _isRecording = false;
      return recordingPath;
    } catch (e) {
      throw Exception('Failed to stop recording: $e');
    }
  }

  Future<void> pauseRecording() async {
    if (!_isRecording) return;

    try {
      if (await _recorder.isRecording()) {
        await _recorder.pause();
      }
    } catch (e) {
      throw Exception('Failed to pause recording: $e');
    }
  }

  Future<void> resumeRecording() async {
    try {
  await _recorder.resume();
    } catch (e) {
      throw Exception('Failed to resume recording: $e');
    }
  }

  Future<void> playAudio(String filePath) async {
    if (_isPlaying) {
      await stopPlaying();
    }

    try {
      await _player.play(DeviceFileSource(filePath));
      _isPlaying = true;
      
      // Listen for completion
      _player.onPlayerComplete.listen((_) {
        _isPlaying = false;
      });
    } catch (e) {
      throw Exception('Failed to play audio: $e');
    }
  }

  Future<void> stopPlaying() async {
    try {
      await _player.stop();
      _isPlaying = false;
    } catch (e) {
      throw Exception('Failed to stop playback: $e');
    }
  }

  Future<void> pausePlaying() async {
    try {
      await _player.pause();
    } catch (e) {
      throw Exception('Failed to pause playback: $e');
    }
  }

  Future<void> resumePlaying() async {
    try {
      await _player.resume();
      _isPlaying = true;
    } catch (e) {
      throw Exception('Failed to resume playback: $e');
    }
  }

  Future<Duration?> getAudioDuration(String filePath) async {
    try {
      await _player.setSource(DeviceFileSource(filePath));
      return await _player.getDuration();
    } catch (e) {
      return null;
    }
  }

  Stream<Duration> getPositionStream() {
    return _player.onPositionChanged;
  }

  Stream<Duration> getDurationStream() {
    return _player.onDurationChanged;
  }

  Future<bool> isAudioFile(String filePath) async {
    final extension = path.extension(filePath).toLowerCase().substring(1);
    return Constants.supportedAudioFormats.contains(extension);
  }

  Future<String> _generateRecordingPath() async {
    final timestamp = DateTime.now().millisecondsSinceEpoch;
    final fileName = 'recording_$timestamp.wav';
    
    // For mobile, use app documents directory
    // For web, this will be handled differently
  if (Platform.isAndroid || Platform.isIOS) {
      final directory = Directory('/storage/emulated/0/Download'); // Android
      if (!await directory.exists()) {
        await directory.create(recursive: true);
      }
      return '${directory.path}/$fileName';
    } else {
      // For other platforms, use current directory
      return fileName;
    }
  }

  void dispose() {
    _recorder.dispose();
    _player.dispose();
  }
}