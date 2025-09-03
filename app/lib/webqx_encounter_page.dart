import 'package:flutter/material.dart';

class WebQxEncounterPage extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Row(
        children: [
          Expanded(flex: 2, child: LeftPanel()),
          Expanded(flex: 5, child: MiddlePanel()),
          Expanded(flex: 3, child: RightPanel()),
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

  final Map<String, Widget> noteSections = {
    'Pre-chart': Text('Pre-charting not available.'),
    'Completed note': Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text('SUBJECTIVE', style: TextStyle(fontWeight: FontWeight.bold)),
        Text(
            'No subjective information was provided during the encounter. The transcript only contains audio testing phrases.'),
        SizedBox(height: 8),
        Text('OBJECTIVE', style: TextStyle(fontWeight: FontWeight.bold)),
        Text('No objective data available from the encounter.'),
        SizedBox(height: 8),
        Text('ASSESSMENT', style: TextStyle(fontWeight: FontWeight.bold)),
        Text(
            'No assessment can be made as no clinical information was discussed.'),
      ],
    ),
    'Dictate': Text('Dictation tools go here.'),
    'Documents': Text('Attached documents will appear here.'),
  };

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
              child: SingleChildScrollView(child: noteSections[selectedTab]!)),
          Divider(),
          Row(
            children: [
              IconButton(onPressed: () {}, icon: Icon(Icons.play_arrow)),
              Text('Play Audio'),
              Spacer(),
              IconButton(onPressed: () {}, icon: Icon(Icons.history)),
              IconButton(onPressed: () {}, icon: Icon(Icons.star_border)),
            ],
          ),
        ],
      ),
    );
  }
}

class RightPanel extends StatelessWidget {
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
          Text('2:01pm — Testing. Hello. Testing. Hello. Hello. Hello.'),
          Divider(),
          Text('ICD-10 Coding', style: Theme.of(context).textTheme.titleMedium),
          SizedBox(height: 8),
          Text('No codes assigned.'),
        ],
      ),
    );
  }
}
