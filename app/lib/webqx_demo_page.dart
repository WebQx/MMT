import 'package:flutter/material.dart';
import 'webqx_encounter_page.dart';

class WebQxDemoPage extends StatelessWidget {
  final List<String> microphoneOptions = [
    'Default - Microphone Array (Intel® Smart Sound Technology (WDM))',
    'External USB Mic',
    'Bluetooth Headset',
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('WebQx MMT'),
        actions: [
          TextButton(onPressed: () {}, child: Text('View Demo')),
          TextButton(onPressed: () {}, child: Text('Upgrade')),
          CircleAvatar(child: Text('NA')),
          SizedBox(width: 12),
        ],
      ),
      body: Center(
        child: DemoModal(microphoneOptions: microphoneOptions),
      ),
    );
  }
}

class DemoModal extends StatefulWidget {
  final List<String> microphoneOptions;
  const DemoModal({required this.microphoneOptions});

  @override
  State<DemoModal> createState() => _DemoModalState();
}

class _DemoModalState extends State<DemoModal> {
  String selectedMic = '';

  @override
  void initState() {
    super.initState();
    selectedMic = widget.microphoneOptions.first;
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 8,
      margin: EdgeInsets.all(24),
      child: Padding(
        padding: EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text('Try a demo session WebQx MMT 🚀',
                style: Theme.of(context).textTheme.headlineSmall),
            SizedBox(height: 12),
            Text('Welcome! 👋', style: Theme.of(context).textTheme.titleMedium),
            SizedBox(height: 8),
            Text(
              'Experience WebQx MMT hands-on and discover its powerful features.\n\nWe can’t wait to see what you’ll create!',
              textAlign: TextAlign.center,
            ),
            SizedBox(height: 24),
            DropdownButtonFormField<String>(
              initialValue: selectedMic,
              items: widget.microphoneOptions
                  .map((mic) => DropdownMenuItem(value: mic, child: Text(mic)))
                  .toList(),
              onChanged: (value) => setState(() => selectedMic = value!),
              decoration: InputDecoration(labelText: 'Select Microphone'),
            ),
            SizedBox(height: 24),
            ElevatedButton.icon(
              onPressed: () {
                Navigator.of(context).push(
                  MaterialPageRoute(
                    builder: (context) => WebQxEncounterPage(),
                  ),
                );
              },
              icon: Icon(Icons.mic),
              label: Text('Start transcribing a demo session'),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.green,
                foregroundColor: Colors.white,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
