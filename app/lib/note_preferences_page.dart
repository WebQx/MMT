import 'package:flutter/material.dart';

class NotePreferencesPage extends StatefulWidget {
  final String userName;
  const NotePreferencesPage({Key? key, required this.userName})
      : super(key: key);

  @override
  _NotePreferencesPageState createState() => _NotePreferencesPageState();
}

class _NotePreferencesPageState extends State<NotePreferencesPage> {
  String selectedFormat = 'Bulleted';

  final Map<String, Widget> hpiExamples = {
    'Bulleted': Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('• Routine follow-up visit'),
        Text(
            '• Chronic conditions: hypertension, hyperlipidemia, obesity, anxiety disorder'),
        Text('• These conditions have remained stable over time'),
        Text('• Ongoing management with treatment plans'),
        Text('• Medical history includes vitamin D deficiency'),
        Text('• Patient reports increased anxiety and trouble sleeping'),
        Text('• Plans as needed'),
        Text(
            '• Assessment of overall health status and new concerns during this visit'),
      ],
    ),
    'Prose': Text(
      'The patient presents for a routine follow-up visit. The patient’s chronic conditions include hypertension, '
      'hyperlipidemia, obesity, and anxiety disorder. These conditions have been mostly clinically stable over time. '
      'The patient is currently undergoing ongoing management with treatment plans. Medical history includes vitamin D deficiency. '
      'Patient reports increased anxiety and trouble sleeping. Regimen plans are made as necessary to meet treatment goals. '
      'Clinician conducts an assessment of the patient’s overall health status and new concerns during this visit to provide '
      'comprehensive and personalized care.',
    ),
  };

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: [
            Text(widget.userName,
                style: const TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(width: 16),
            const Text('Encounters'),
          ],
        ),
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Setup your note preferences',
                style: Theme.of(context).textTheme.headlineSmall),
            const SizedBox(height: 16),
            const Text('How would you like the HPI section to be formatted?'),
            const SizedBox(height: 8),
            ToggleButtons(
              isSelected: ['Bulleted', 'Prose']
                  .map((f) => f == selectedFormat)
                  .toList(),
              onPressed: (index) {
                setState(() {
                  selectedFormat = ['Bulleted', 'Prose'][index];
                });
              },
              children: const [Text('Bulleted'), Text('Prose')],
            ),
            const SizedBox(height: 24),
            Text('Preview:', style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 8),
            hpiExamples[selectedFormat]!,
          ],
        ),
      ),
    );
  }
}
