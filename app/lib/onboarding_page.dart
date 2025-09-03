import 'package:flutter/material.dart';
import 'note_preferences_page.dart';

class OnboardingPage extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    final nameController = TextEditingController();
    final orgController = TextEditingController();
    final roleController = TextEditingController();
    return Scaffold(
      backgroundColor: const Color(0xFFF5F6FA),
      appBar: AppBar(
        title: const Text('Account Setup'),
        backgroundColor: Colors.blueAccent,
      ),
      body: Center(
        child: Card(
          elevation: 8,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
          ),
          child: Padding(
            padding: const EdgeInsets.all(32.0),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    _stepCircle(true),
                    _stepLine(),
                    _stepCircle(false),
                    _stepLine(),
                    _stepCircle(false),
                  ],
                ),
                const SizedBox(height: 24),
                Text('Welcome! Let’s set up your account.',
                    style: TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                        color: Colors.blueAccent)),
                const SizedBox(height: 16),
                Text('Please provide your details to get started.'),
                const SizedBox(height: 24),
                TextField(
                  controller: nameController,
                  decoration: InputDecoration(
                    labelText: 'Full Name',
                    border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(8)),
                  ),
                ),
                const SizedBox(height: 16),
                TextField(
                  controller: orgController,
                  decoration: InputDecoration(
                    labelText: 'Organization',
                    border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(8)),
                  ),
                ),
                const SizedBox(height: 16),
                TextField(
                  controller: roleController,
                  decoration: InputDecoration(
                    labelText: 'Role',
                    border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(8)),
                  ),
                ),
                const SizedBox(height: 32),
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.blueAccent,
                      shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(8)),
                      padding: const EdgeInsets.symmetric(vertical: 16),
                    ),
                    onPressed: () {
                      Navigator.of(context).push(
                        MaterialPageRoute(
                          builder: (context) => NotePreferencesPage(
                              userName: nameController.text.isEmpty
                                  ? 'User'
                                  : nameController.text),
                        ),
                      );
                    },
                    child:
                        const Text('Continue', style: TextStyle(fontSize: 16)),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

Widget _stepCircle(bool active) {
  return Container(
    width: 24,
    height: 24,
    decoration: BoxDecoration(
      color: active ? Colors.blueAccent : Colors.grey[300],
      shape: BoxShape.circle,
    ),
    child:
        active ? const Icon(Icons.check, color: Colors.white, size: 16) : null,
  );
}

Widget _stepLine() {
  return Container(
    width: 32,
    height: 2,
    color: Colors.grey[300],
  );
}
