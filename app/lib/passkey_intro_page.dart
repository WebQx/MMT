import 'package:flutter/material.dart';
import 'onboarding_page.dart';

class PasskeyIntroPage extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF5F6FA),
      appBar: AppBar(
        title: const Text('Sign Up - Passkeys'),
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
                    Icon(Icons.key, size: 40, color: Colors.blueAccent),
                    const SizedBox(width: 12),
                    Text('Use passkeys for easier and more secure sign in',
                        style: TextStyle(
                            fontSize: 20,
                            fontWeight: FontWeight.bold,
                            color: Colors.blueAccent)),
                  ],
                ),
                const SizedBox(height: 24),
                _featureRow('Better, faster sign in',
                    'Easily login to your account in one step.'),
                const SizedBox(height: 16),
                _featureRow('Safer by design',
                    "Passkeys can't be guessed, leaked, or even phished"),
                const SizedBox(height: 16),
                _featureRow('Passkeys are easy to use',
                    'You can use Touch ID, Face ID, Windows Hello and more'),
                const SizedBox(height: 32),
                Row(
                  children: [
                    Checkbox(value: false, onChanged: (v) {}),
                    const Text("Don't ask me again"),
                  ],
                ),
                const SizedBox(height: 24),
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
                          builder: (context) => OnboardingPage(),
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

Widget _featureRow(String title, String description) {
  return Row(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Icon(Icons.check_circle, color: Colors.green, size: 24),
      const SizedBox(width: 8),
      Expanded(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title, style: TextStyle(fontWeight: FontWeight.bold)),
            Text(description),
          ],
        ),
      ),
    ],
  );
}
