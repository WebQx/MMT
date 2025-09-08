import 'dart:io';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:file_picker/file_picker.dart';
import '../providers/app_state_provider.dart';
import '../services/audio_service.dart';
import '../services/transcription_service.dart';
import '../models/transcription_result.dart';
import '../utils/constants.dart';

class TranscriptionScreen extends StatefulWidget {
  const TranscriptionScreen({Key? key}) : super(key: key);

  @override
  State<TranscriptionScreen> createState() => _TranscriptionScreenState();
}

class _TranscriptionScreenState extends State<TranscriptionScreen> {
  final TextEditingController _resultController = TextEditingController();
  final TextEditingController _promptController = TextEditingController();
  
  bool _isTranscribing = false;
  TranscriptionResult? _currentResult;
  File? _selectedFile;
  
  @override
  void dispose() {
    _resultController.dispose();
    _promptController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Transcription'),
        actions: [
          if (_currentResult != null)
            IconButton(
              icon: const Icon(Icons.share),
              onPressed: _shareResult,
            ),
        ],
      ),
      body: Consumer<AppStateProvider>(
        builder: (context, appState, _) {
          return SingleChildScrollView(
            padding: const EdgeInsets.all(Constants.padding),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Current Settings
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(Constants.padding),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'Current Settings',
                          style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                        const SizedBox(height: 12),
                        _SettingRow(
                          label: 'Type',
                          value: appState.selectedTranscriptionType,
                        ),
                        _SettingRow(
                          label: 'Network',
                          value: appState.selectedNetworkMode,
                        ),
                        _SettingRow(
                          label: 'Language',
                          value: appState.selectedLanguage == 'auto' 
                            ? 'Auto-detect' 
                            : appState.selectedLanguage.toUpperCase(),
                        ),
                      ],
                    ),
                  ),
                ),
                
                const SizedBox(height: 24),
                
                // Audio Input Section
                const Text(
                  'Audio Input',
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 16),
                
                // Recording Controls
                Consumer<AudioService>(
                  builder: (context, audioService, _) {
                    return Card(
                      child: Padding(
                        padding: const EdgeInsets.all(Constants.padding),
                        child: Column(
                          children: [
                            // Record Button
                            Row(
                              children: [
                                Expanded(
                                  child: ElevatedButton.icon(
                                    onPressed: audioService.isRecording 
                                      ? _stopRecording 
                                      : _startRecording,
                                    icon: Icon(
                                      audioService.isRecording 
                                        ? Icons.stop 
                                        : Icons.mic,
                                    ),
                                    label: Text(
                                      audioService.isRecording 
                                        ? 'Stop Recording' 
                                        : 'Start Recording',
                                    ),
                                    style: ElevatedButton.styleFrom(
                                      backgroundColor: audioService.isRecording 
                                        ? Constants.errorColor 
                                        : Constants.primaryColor,
                                    ),
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 16),
                            
                            // File Selection
                            Row(
                              children: [
                                Expanded(
                                  child: OutlinedButton.icon(
                                    onPressed: _selectFile,
                                    icon: const Icon(Icons.file_upload),
                                    label: Text(
                                      _selectedFile != null 
                                        ? 'File Selected' 
                                        : 'Select Audio File',
                                    ),
                                  ),
                                ),
                              ],
                            ),
                            
                            if (_selectedFile != null) ...[
                              const SizedBox(height: 8),
                              Text(
                                'Selected: ${_selectedFile!.path.split('/').last}',
                                style: const TextStyle(
                                  fontSize: 12,
                                  color: Colors.grey,
                                ),
                              ),
                            ],
                          ],
                        ),
                      ),
                    );
                  },
                ),
                
                const SizedBox(height: 24),
                
                // Prompt Input
                const Text(
                  'Additional Context (Optional)',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 8),
                TextField(
                  controller: _promptController,
                  decoration: const InputDecoration(
                    hintText: 'Enter context or keywords to improve transcription accuracy...',
                    helperText: 'Provide medical terms or context that might help',
                  ),
                  maxLines: 3,
                ),
                
                const SizedBox(height: 24),
                
                // Transcribe Button
                Row(
                  children: [
                    Expanded(
                      child: ElevatedButton.icon(
                        onPressed: _canTranscribe() && !_isTranscribing 
                          ? _transcribe 
                          : null,
                        icon: _isTranscribing 
                          ? const SizedBox(
                              width: 20,
                              height: 20,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            )
                          : const Icon(Icons.transcribe),
                        label: Text(
                          _isTranscribing 
                            ? 'Transcribing...' 
                            : 'Transcribe Audio',
                        ),
                      ),
                    ),
                  ],
                ),
                
                const SizedBox(height: 24),
                
                // Results Section
                if (_currentResult != null || _resultController.text.isNotEmpty) ...[
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text(
                        'Transcription Result',
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      Row(
                        children: [
                          IconButton(
                            icon: const Icon(Icons.copy),
                            onPressed: _copyResult,
                            tooltip: 'Copy to clipboard',
                          ),
                          IconButton(
                            icon: const Icon(Icons.clear),
                            onPressed: _clearResult,
                            tooltip: 'Clear result',
                          ),
                        ],
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  
                  // Result Card
                  Card(
                    child: Padding(
                      padding: const EdgeInsets.all(Constants.padding),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          if (_currentResult != null) ...[
                            Row(
                              children: [
                                Icon(
                                  Icons.info_outline,
                                  size: 16,
                                  color: Colors.grey[600],
                                ),
                                const SizedBox(width: 4),
                                Text(
                                  'Language: ${_currentResult!.language.toUpperCase()} • '
                                  'Confidence: ${(_currentResult!.confidence * 100).toStringAsFixed(1)}%',
                                  style: TextStyle(
                                    fontSize: 12,
                                    color: Colors.grey[600],
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 8),
                          ],
                          
                          TextField(
                            controller: _resultController,
                            decoration: const InputDecoration(
                              hintText: 'Transcription will appear here...',
                              border: InputBorder.none,
                            ),
                            maxLines: null,
                            minLines: 5,
                          ),
                        ],
                      ),
                    ),
                  ),
                  
                  const SizedBox(height: 16),
                  
                  // Action Buttons
                  Row(
                    children: [
                      Expanded(
                        child: OutlinedButton.icon(
                          onPressed: _printResult,
                          icon: const Icon(Icons.print),
                          label: const Text('Print'),
                        ),
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: OutlinedButton.icon(
                          onPressed: _emailResult,
                          icon: const Icon(Icons.email),
                          label: const Text('Email'),
                        ),
                      ),
                    ],
                  ),
                ],
              ],
            ),
          );
        },
      ),
    );
  }

  bool _canTranscribe() {
    final audioService = Provider.of<AudioService>(context, listen: false);
    return _selectedFile != null || audioService.currentRecordingPath != null;
  }

  Future<void> _startRecording() async {
    try {
      final audioService = Provider.of<AudioService>(context, listen: false);
      await audioService.startRecording();
      setState(() {});
    } catch (e) {
      _showError('Failed to start recording: $e');
    }
  }

  Future<void> _stopRecording() async {
    try {
      final audioService = Provider.of<AudioService>(context, listen: false);
      final recordingPath = await audioService.stopRecording();
      
      if (recordingPath != null) {
        setState(() {
          _selectedFile = File(recordingPath);
        });
      }
    } catch (e) {
      _showError('Failed to stop recording: $e');
    }
  }

  Future<void> _selectFile() async {
    try {
      final result = await FilePicker.platform.pickFiles(
        type: FileType.audio,
        allowMultiple: false,
      );

      if (result != null && result.files.single.path != null) {
        setState(() {
          _selectedFile = File(result.files.single.path!);
        });
      }
    } catch (e) {
      _showError('Failed to select file: $e');
    }
  }

  Future<void> _transcribe() async {
    if (_selectedFile == null) return;

    setState(() {
      _isTranscribing = true;
    });

    try {
      final appState = Provider.of<AppStateProvider>(context, listen: false);
      final transcriptionService = Provider.of<TranscriptionService>(context, listen: false);
      
      final authToken = appState.authToken!;
      final language = appState.selectedLanguage;
      final prompt = _promptController.text.isNotEmpty ? _promptController.text : null;
      
      TranscriptionResult result;
      
      // Choose transcription method based on settings
      if (appState.selectedTranscriptionType == 'Real-time Transcription' ||
          appState.selectedTranscriptionType == 'Ambient Mode') {
        result = await transcriptionService.transcribeCloud(
          audioFile: _selectedFile!,
          authToken: authToken,
          language: language,
          prompt: prompt,
        );
      } else {
        result = await transcriptionService.transcribeLocal(
          audioFile: _selectedFile!,
          authToken: authToken,
          language: language,
          prompt: prompt,
        );
      }
      
      setState(() {
        _currentResult = result;
        _resultController.text = result.text;
      });
      
      _showSuccess('Transcription completed successfully!');
      
    } catch (e) {
      _showError('Transcription failed: $e');
    } finally {
      setState(() {
        _isTranscribing = false;
      });
    }
  }

  void _copyResult() {
    // Copy to clipboard functionality
    _showSuccess('Copied to clipboard');
  }

  void _clearResult() {
    setState(() {
      _currentResult = null;
      _resultController.clear();
    });
  }

  void _shareResult() {
    // Share functionality
    _showSuccess('Sharing...');
  }

  void _printResult() {
    // Print functionality
    _showSuccess('Printing...');
  }

  void _emailResult() {
    // Email functionality
    _showSuccess('Opening email...');
  }

  void _showError(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Constants.errorColor,
      ),
    );
  }

  void _showSuccess(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Constants.successColor,
      ),
    );
  }
}

class _SettingRow extends StatelessWidget {
  final String label;
  final String value;

  const _SettingRow({
    required this.label,
    required this.value,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            label,
            style: const TextStyle(color: Colors.grey),
          ),
          Text(
            value,
            style: const TextStyle(fontWeight: FontWeight.w500),
          ),
        ],
      ),
    );
  }
}