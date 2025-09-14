import 'package:flutter/material.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;
import 'utils/constants.dart';

class UpgradePage extends StatelessWidget {
  Future<String> assignTier({
    required String email,
    required String ipAddress,
    required String keycloakId,
  }) async {
    final String backendUrl = '${Constants.baseUrl}/assign-tier';
    final response = await http.post(
      Uri.parse(backendUrl),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'email': email,
        'ip_address': ipAddress,
        'keycloak_id': keycloakId,
      }),
    );
    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      return data['assigned_tier'] ?? 'Unknown';
    } else {
      throw Exception('Failed to assign tier: ${response.body}');
    }
  }

  final List<Map<String, dynamic>> plans = [
    {
      'title': 'Tier 1 – Developed Countries',
      'price': '480/clinician/year',
      'features': [
        'Full access after 1-month free trial',
        'Unlimited encounters',
        'ICD-10 Coding & Dictation',
        'Template Exchange & Auto Template',
        'Zoom Telehealth Integration',
        'Live Chat Support',
        'EHR Write-back',
      ],
    },
    {
      'title': 'Tier 2 – Underserved Regions',
      'price': '180/clinician/year',
      'features': [
        'Full access after 1-month free trial',
        'Unlimited encounters',
        'Dictation & Patient Context',
        'Auto Template & Source View',
        'Basic Support',
      ],
    },
    {
      'title': 'Tier 3 – MUP Access',
      'price': 'Free',
      'features': [
        'Full access during trial',
        'Unlimited encounters',
        'Basic dictation & sharing',
        'Data retention',
        'Community support only',
      ],
    },
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Upgrade WebQx MMT')),
      body: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          children: [
            Card(
              color: Colors.green.shade50,
              child: Padding(
                padding: EdgeInsets.all(16),
                child: Column(
                  children: [
                    Text('🎉 1-Month Free Trial',
                        style: Theme.of(context).textTheme.headlineSmall),
                    SizedBox(height: 8),
                    Text(
                        'Enjoy full access to all features for 30 days. No credit card required.'),
                    SizedBox(height: 8),
                    ElevatedButton(
                        onPressed: () async {
                          try {
                            String tier = await assignTier(
                              email: 'user@example.com',
                              ipAddress: '8.8.8.8', // Replace with actual IP
                              keycloakId: 'your-keycloak-id',
                            );
                            ScaffoldMessenger.of(context).showSnackBar(
                              SnackBar(content: Text('Assigned Tier: $tier')),
                            );
                          } catch (e) {
                            ScaffoldMessenger.of(context).showSnackBar(
                              SnackBar(content: Text('Error: $e')),
                            );
                          }
                        },
                        child: Text('Start Free Trial')),
                  ],
                ),
              ),
            ),
            SizedBox(height: 24),
            Expanded(
              child: ListView.builder(
                itemCount: plans.length,
                itemBuilder: (context, index) {
                  final plan = plans[index];
                  return Card(
                    margin: EdgeInsets.symmetric(vertical: 8),
                    child: Padding(
                      padding: EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(plan['title'],
                              style: Theme.of(context).textTheme.titleLarge),
                          SizedBox(height: 4),
                          Text(plan['price'],
                              style: TextStyle(
                                  fontSize: 16, fontWeight: FontWeight.bold)),
                          SizedBox(height: 8),
                          ...plan['features']
                              .map<Widget>((f) => Text('• $f'))
                              .toList(),
                          SizedBox(height: 12),
                          ElevatedButton(
                            onPressed: () {},
                            child: Text(index == 2
                                ? 'Activate Free Access'
                                : 'Upgrade Now'),
                          ),
                        ],
                      ),
                    ),
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }
}
