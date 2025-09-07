import 'package:flutter/material.dart';

/// A simple, responsive marketing-style home page that appears before the
/// login flow. Contains hero, features, and CTAs (Get started / Learn more).
class HomePage extends StatelessWidget {
  final VoidCallback onGetStarted;
  final VoidCallback? onLearnMore;

  const HomePage({super.key, required this.onGetStarted, this.onLearnMore});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              // Hero
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 56),
                color: Colors.white,
                child: ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 1100),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.center,
                    children: [
                      Expanded(
                        flex: 6,
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text('Ambient clinical transcription, reimagined',
                                style: theme.textTheme.headline4?.copyWith(fontWeight: FontWeight.bold)),
                            const SizedBox(height: 12),
                            Text(
                              'Capture patient conversations, summarize notes, and integrate with EHRs — fast and securely.',
                              style: theme.textTheme.subtitle1,
                            ),
                            const SizedBox(height: 24),
                            Row(children: [
                              ElevatedButton(
                                onPressed: onGetStarted,
                                child: const Padding(
                                  padding: EdgeInsets.symmetric(horizontal: 18.0, vertical: 14.0),
                                  child: Text('Get started', style: TextStyle(fontSize: 16)),
                                ),
                              ),
                              const SizedBox(width: 12),
                              OutlinedButton(
                                onPressed: onLearnMore,
                                child: const Padding(
                                  padding: EdgeInsets.symmetric(horizontal: 14.0, vertical: 14.0),
                                  child: Text('Learn more', style: TextStyle(fontSize: 16)),
                                ),
                              ),
                            ])
                          ],
                        ),
                      ),
                      const SizedBox(width: 24),
                      // Illustration / placeholder
                      Expanded(
                        flex: 4,
                        child: AspectRatio(
                          aspectRatio: 4 / 3,
                          child: Container(
                            decoration: BoxDecoration(
                              color: Colors.blue.shade50,
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: Center(
                              child: Icon(Icons.speaker_notes, size: 96, color: Colors.blue.shade300),
                            ),
                          ),
                        ),
                      )
                    ],
                  ),
                ),
              ),

              const SizedBox(height: 28),

              // Features
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 24.0),
                child: ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 1100),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      Text('Why MMT', style: theme.textTheme.headline6),
                      const SizedBox(height: 12),
                      Wrap(
                        spacing: 16,
                        runSpacing: 16,
                        children: const [
                          _FeatureCard(title: 'Ambient capture', body: 'Automatically capture patient visits with low friction.'),
                          _FeatureCard(title: 'EHR integrations', body: 'Push notes to OpenEMR and other EHRs.'),
                          _FeatureCard(title: 'HIPAA-aware', body: 'Security-first design and audit logging.'),
                          _FeatureCard(title: 'On-device or cloud', body: 'Choose local Whisper or OpenAI Whisper.'),
                        ],
                      ),
                      const SizedBox(height: 36),
                    ],
                  ),
                ),
              ),

              // Footer CTA band
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 32),
                color: Colors.grey.shade50,
                child: ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 1100),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text('Ready to try MMT?', style: theme.textTheme.headline6),
                            const SizedBox(height: 6),
                            Text('Sign in or continue as a guest to explore the demo.', style: theme.textTheme.bodyText2),
                          ],
                        ),
                      ),
                      const SizedBox(width: 18),
                      Row(children: [
                        ElevatedButton(onPressed: onGetStarted, child: const Text('Get started')),
                      ])
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _FeatureCard extends StatelessWidget {
  final String title;
  final String body;
  const _FeatureCard({required this.title, required this.body});

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 260,
      child: Card(
        elevation: 2,
        child: Padding(
          padding: const EdgeInsets.all(12.0),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(title, style: Theme.of(context).textTheme.subtitle1?.copyWith(fontWeight: FontWeight.bold)),
            const SizedBox(height: 6),
            Text(body, style: Theme.of(context).textTheme.bodyText2),
          ]),
        ),
      ),
    );
  }
}
