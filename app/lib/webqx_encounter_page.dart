import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'dart:io';
// ...existing imports...

import 'package:file_picker/file_picker.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter/services.dart';
import 'package:printing/printing.dart';
import 'package:pdf/widgets.dart' as pw;
import 'package:speech_to_text/speech_to_text.dart' as stt;

import 'services/transcription_service.dart';
import 'utils/constants.dart';
import 'models/transcription_result.dart';

class WebQxEncounterPage extends StatefulWidget {
  @override
  _WebQxEncounterPageState createState() => _WebQxEncounterPageState();
}

class _WebQxEncounterPageState extends State<WebQxEncounterPage> {
  String _transcript = '';
  String _icd10Codes = 'No codes assigned.';

  void _handleTranscriptUpdate(String t) {
    setState(() => _transcript = t);
  }

  void _handleIcdUpdate(String codes) {
    setState(
        () => _icd10Codes = codes.isNotEmpty ? codes : 'No codes assigned.');
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Row(
        children: [
          Expanded(flex: 2, child: LeftPanel()),
          Expanded(
              flex: 5,
              child: MiddlePanel(
                  onTranscript: _handleTranscriptUpdate,
                  onIcdCodes: _handleIcdUpdate)),
          Expanded(
              flex: 3,
              child:
                  RightPanel(transcript: _transcript, icd10Codes: _icd10Codes)),
        ],
      ),
    );
  }
}

class LeftPanel extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Container(
      color: Colors.grey.shade100,
      padding: EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Patient: Naveed Ahmad',
              style: TextStyle(fontWeight: FontWeight.bold)),
          SizedBox(height: 8),
          Text('Encounter Demo - 9/13'),
          Text('Status: Completed'),
          Text('Sep 13, 2023 • 2:01 PM'),
          SizedBox(height: 16),
          VisitTypeSelector(),
          SizedBox(height: 16),
          ElevatedButton(onPressed: () {}, child: Text('Retry Demo')),
        ],
      ),
    );
  }
}

class VisitTypeSelector extends StatefulWidget {
  @override
  _VisitTypeSelectorState createState() => _VisitTypeSelectorState();
}

class _VisitTypeSelectorState extends State<VisitTypeSelector> {
  String _visitType = 'In-Clinic';
  final _videoLinkController = TextEditingController();
  final _connectionNotesController = TextEditingController();

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Text('Visit Type:'),
            SizedBox(width: 8),
            DropdownButton<String>(
              value: _visitType,
              items: [
                DropdownMenuItem(value: 'In-Clinic', child: Text('In-Clinic')),
                DropdownMenuItem(
                    value: 'Telehealth', child: Text('Telehealth')),
              ],
              onChanged: (v) => setState(() => _visitType = v ?? 'In-Clinic'),
            ),
          ],
        ),
        if (_visitType == 'Telehealth') ...[
          SizedBox(height: 8),
          TextField(
              controller: _videoLinkController,
              decoration: InputDecoration(labelText: 'Video link (optional)')),
          SizedBox(height: 8),
          TextField(
              controller: _connectionNotesController,
              decoration: InputDecoration(labelText: 'Connection notes')),
        ]
      ],
    );
  }
}

class MiddlePanel extends StatefulWidget {
  final void Function(String)? onTranscript;
  final void Function(String)? onIcdCodes;
  MiddlePanel({this.onTranscript, this.onIcdCodes});

  @override
  _MiddlePanelState createState() => _MiddlePanelState();
}

class _MiddlePanelState extends State<MiddlePanel> {
  String selectedTab = 'Completed note';
  String subjective = '';
  String objective = '';
  String assessment = '';
  String plan = '';
  // Live speech recognition / transcription
  late stt.SpeechToText _speech;
  bool _speechAvailable = false;
  bool _isListening = false;
  String _liveTranscript = '';
  final _transcriptionService = TranscriptionService();
  final _secureStorage = const FlutterSecureStorage();

  Widget getNoteSection(String tab) {
    switch (tab) {
      case 'Pre-chart':
        return Text('Pre-charting not available.');
      case 'Completed note':
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('SUBJECTIVE', style: TextStyle(fontWeight: FontWeight.bold)),
            TextField(
              decoration: InputDecoration(hintText: 'Enter subjective info'),
              controller: TextEditingController(text: subjective),
              onChanged: (v) => setState(() => subjective = v),
              maxLines: 2,
            ),
            SizedBox(height: 8),
            Text('OBJECTIVE', style: TextStyle(fontWeight: FontWeight.bold)),
            TextField(
              decoration: InputDecoration(hintText: 'Enter objective info'),
              controller: TextEditingController(text: objective),
              onChanged: (v) => setState(() => objective = v),
              maxLines: 2,
            ),
            SizedBox(height: 8),
            Text('ASSESSMENT', style: TextStyle(fontWeight: FontWeight.bold)),
            TextField(
              decoration: InputDecoration(hintText: 'Enter assessment'),
              controller: TextEditingController(text: assessment),
              onChanged: (v) => setState(() => assessment = v),
              maxLines: 2,
            ),
            SizedBox(height: 8),
            Text('PLAN', style: TextStyle(fontWeight: FontWeight.bold)),
            TextField(
              decoration: InputDecoration(hintText: 'Enter plan'),
              controller: TextEditingController(text: plan),
              onChanged: (v) => setState(() => plan = v),
              maxLines: 2,
            ),
          ],
        );
      case 'Dictate':
        return Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Live Recognition',
                style: TextStyle(fontWeight: FontWeight.bold)),
            SizedBox(height: 8),
            if (kIsWeb)
              Text(
                  'Live recognition is not available on Web. Use "Upload audio file" below.')
            else ...[
              ElevatedButton.icon(
                icon: Icon(_isListening ? Icons.stop : Icons.mic),
                label: Text(_isListening
                    ? 'Stop Live Recognition'
                    : 'Start Live Recognition'),
                onPressed: () async {
                  if (!_speechAvailable) {
                    _speechAvailable = await _speech.initialize(
                        onStatus: (s) {}, onError: (e) {});
                  }
                  if (_isListening) {
                    _speech.stop();
                    setState(() => _isListening = false);
                  } else {
                    _speech.listen(onResult: (r) {
                      setState(() {
                        _liveTranscript = r.recognizedWords;
                      });
                    });
                    setState(() => _isListening = true);
                  }
                },
              ),
              SizedBox(height: 8),
              Text('Live transcript:'),
              Container(
                width: double.infinity,
                padding: EdgeInsets.all(8),
                color: Colors.white,
                child: Text(_liveTranscript.isNotEmpty ? _liveTranscript : '—'),
              ),
            ],
            SizedBox(height: 16),
            Text('Upload audio file for backend transcription',
                style: TextStyle(fontWeight: FontWeight.bold)),
            SizedBox(height: 8),
            ElevatedButton.icon(
              icon: Icon(Icons.upload_file),
              label: Text('Pick audio file'),
              onPressed: () async {
                try {
                  final result = await FilePicker.platform.pickFiles(
                      type: FileType.custom,
                      allowedExtensions: Constants.supportedAudioFormats);
                  if (result == null) return;
                  final authToken =
                      await _secureStorage.read(key: Constants.authTokenKey);
                  if (authToken == null) {
                    ScaffoldMessenger.of(context).showSnackBar(SnackBar(
                        content: Text('Auth token missing. Please login.')));
                    return;
                  }
                  ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text('Uploading and transcribing...')));
                  TranscriptionResult tr;
                  if (kIsWeb) {
                    final bytes = result.files.single.bytes;
                    if (bytes == null) {
                      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
                          content:
                              Text('Unable to read file bytes in browser.')));
                      return;
                    }
                    tr = await _transcriptionService.transcribeCloudJson(
                        audioBytes: bytes, authToken: authToken);
                  } else {
                    final path = result.files.single.path;
                    if (path == null) return;
                    final file = File(path);
                    tr = await _transcriptionService.transcribeLocal(
                        audioFile: file, authToken: authToken);
                  }
                  setState(() {
                    // place transcription into live transcript and into subjective by default
                    _liveTranscript = tr.text;
                    subjective = subjective.isEmpty ? tr.text : subjective;
                  });
                  // notify parent
                  if (widget.onTranscript != null)
                    widget.onTranscript!(_liveTranscript);
                  ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text('Transcription complete')));
                } catch (e) {
                  ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text('Transcription failed: $e')));
                }
              },
            ),
            SizedBox(height: 12),
            ElevatedButton.icon(
              icon: Icon(Icons.auto_fix_high),
              label: Text('Auto-populate SOAP from Transcript'),
              onPressed: _liveTranscript.isEmpty
                  ? null
                  : () async {
                      final authToken = await _secureStorage.read(
                          key: Constants.authTokenKey);
                      if (authToken == null) {
                        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
                            content:
                                Text('Auth token missing. Please login.')));
                        return;
                      }
                      try {
                        ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(content: Text('Parsing transcript...')));
                        final Map<String, dynamic> parsed =
                            await _transcriptionService.parseChart(
                                authToken: authToken, text: _liveTranscript);
                        setState(() {
                          subjective = parsed['subjective'] ?? subjective;
                          objective = parsed['objective'] ?? objective;
                          assessment = parsed['assessment'] ?? assessment;
                          plan = parsed['plan'] ?? plan;
                        });
                        if (parsed.containsKey('icd10') &&
                            widget.onIcdCodes != null) {
                          final codes = (parsed['icd10'] is List)
                              ? (parsed['icd10'] as List).join(', ')
                              : parsed['icd10'].toString();
                          widget.onIcdCodes!(codes);
                        }
                        ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(content: Text('SOAP fields updated')));
                      } catch (e) {
                        ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(content: Text('Parsing failed: $e')));
                      }
                    },
            ),
          ],
        );
      case 'Documents':
        return Text('Attached documents will appear here.');
      default:
        return SizedBox.shrink();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.all(16),
      child: Column(
        children: [
          Row(
            children: ['Pre-chart', 'Completed note', 'Dictate', 'Documents']
                .map((tab) => Padding(
                      padding: EdgeInsets.only(right: 12),
                      child: ChoiceChip(
                        label: Text(tab),
                        selected: selectedTab == tab,
                        onSelected: (_) => setState(() => selectedTab = tab),
                      ),
                    ))
                .toList(),
          ),
          SizedBox(height: 16),
          Expanded(
              child: SingleChildScrollView(child: getNoteSection(selectedTab))),
          Divider(),
          Row(
            children: [
              IconButton(onPressed: () {}, icon: Icon(Icons.play_arrow)),
              Text('Play Audio'),
              Spacer(),
              IconButton(onPressed: () {}, icon: Icon(Icons.history)),
              IconButton(onPressed: () {}, icon: Icon(Icons.star_border)),
              ElevatedButton(
                onPressed: () {
                  final note =
                      '''SUBJECTIVE:\n$subjective\n\nOBJECTIVE:\n$objective\n\nASSESSMENT:\n$assessment\n\nPLAN:\n$plan''';
                  showDialog(
                    context: context,
                    builder: (ctx) => AlertDialog(
                      title: Text('Finalized Note'),
                      content: SingleChildScrollView(child: Text(note)),
                      actions: [
                        TextButton(
                          onPressed: () => Navigator.pop(ctx),
                          child: Text('Close'),
                        ),
                        TextButton(
                          onPressed: () async {
                            // Copy to clipboard
                            await Clipboard.setData(ClipboardData(text: note));
                            // Create a simple PDF and offer print/share
                            try {
                              final doc = pw.Document();
                              doc.addPage(pw.Page(
                                  build: (pw.Context c) => pw.Text(note)));
                              final bytes = await doc.save();
                              await Printing.layoutPdf(
                                  onLayout: (_) async => bytes);
                            } catch (e) {
                              // If PDF generation fails, still close and notify
                              ScaffoldMessenger.of(ctx).showSnackBar(
                                  SnackBar(content: Text('Export failed: $e')));
                            }
                            Navigator.pop(ctx);
                          },
                          child: Text('Export'),
                        ),
                      ],
                    ),
                  );
                },
                child: Text('Finalize Note'),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class RightPanel extends StatelessWidget {
  final String transcript;
  final String icd10Codes;
  const RightPanel(
      {this.transcript = '', this.icd10Codes = 'No codes assigned.'});

  @override
  Widget build(BuildContext context) {
    return Container(
      color: Colors.grey.shade50,
      padding: EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Transcript', style: Theme.of(context).textTheme.titleMedium),
          SizedBox(height: 8),
          Text(transcript.isNotEmpty ? transcript : 'No transcript available.'),
          Divider(),
          Text('ICD-10 Coding', style: Theme.of(context).textTheme.titleMedium),
          SizedBox(height: 8),
          Text(icd10Codes),
        ],
      ),
    );
  }
}
