import 'package:flutter/material.dart';

class WebQxEncounterPage extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    // For demo, pass empty transcript and codes; will be connected to MiddlePanel state later
    return Scaffold(
      body: Row(
        children: [
          Expanded(flex: 2, child: LeftPanel()),
          Expanded(flex: 5, child: MiddlePanel()),
          Expanded(
              flex: 3,
              child:
                  RightPanel(transcript: '', icd10Codes: 'No codes assigned.')),
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
          Row(
            children: [
              Text('Visit Type:'),
              SizedBox(width: 8),
              DropdownButton<String>(
                value: 'In-Clinic',
                items: [
                  DropdownMenuItem(
                      value: 'In-Clinic', child: Text('In-Clinic')),
                  DropdownMenuItem(
                      value: 'Telehealth', child: Text('Telehealth'))
                ],
                onChanged: (v) {},
              ),
            ],
          ),
          SizedBox(height: 16),
          ElevatedButton(onPressed: () {}, child: Text('Retry Demo')),
        ],
      ),
    );
  }
}

class MiddlePanel extends StatefulWidget {
  @override
  _MiddlePanelState createState() => _MiddlePanelState();
}

class _MiddlePanelState extends State<MiddlePanel> {
  String selectedTab = 'Completed note';
  String subjective = '';
  String objective = '';
  String assessment = '';
  String plan = '';

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
        return Text('Dictation tools go here.');
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
                          onPressed: () {
                            // TODO: Implement export/print/share
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
