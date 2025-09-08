import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/app_state_provider.dart';
import '../utils/i18n.dart';

/// A composable login card used by the main app. It mirrors a modern, centered
/// sign-in page with email/password fields, OAuth sign-in button, guest CTA,
/// and helpful links (Sign up / Forgot password).
class LoginCard extends StatefulWidget {
  final VoidCallback onKeycloak;
  final VoidCallback onGoogle;
  final VoidCallback onMicrosoft;
  final VoidCallback onApple;
  final VoidCallback onGuest;
  final void Function(String email, String password) onLocalLogin;
  final VoidCallback? onBack;
  final VoidCallback onSignUp;
  final void Function(String language) onLanguageChanged;
  final String resultText;
  final bool isLoading;

  const LoginCard({
    super.key,
  required this.onKeycloak,
  required this.onGoogle,
  required this.onMicrosoft,
  required this.onApple,
    required this.onGuest,
    required this.onLocalLogin,
  this.onBack,
  required this.onSignUp,
  required this.onLanguageChanged,
    this.resultText = '',
    this.isLoading = false,
  });

  @override
  State<LoginCard> createState() => _LoginCardState();
}

class _LoginCardState extends State<LoginCard> {
  final TextEditingController _emailController = TextEditingController();
  final TextEditingController _passwordController = TextEditingController();
  bool _obscure = true;
  String _selectedLanguage = 'en';

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Center(
      child: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 24.0, vertical: 24.0),
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 520),
          child: Card(
            elevation: 10,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            child: Padding(
              padding: const EdgeInsets.all(28.0),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  if (widget.onBack != null) ...[
                    Align(
                      alignment: Alignment.topLeft,
                      child: IconButton(
                        icon: const Icon(Icons.arrow_back),
                        onPressed: widget.onBack,
                      ),
                    ),
                    const SizedBox(height: 6),
                  ],
                  // Brand
                  Column(
                    children: [
                      const Icon(Icons.health_and_safety, size: 56, color: Colors.blueAccent),
                      const SizedBox(height: 8),
                      Text('WebQx Multilingual Medical Transcription (MMT)', style: theme.textTheme.titleLarge?.copyWith(fontWeight: FontWeight.bold)),
                    ],
                  ),
                  const SizedBox(height: 20),

                  // Email field
                  // Language selector
                  Row(
                    children: [
                      Text(I18n.t('language', _selectedLanguage)),
                      const SizedBox(width: 8),
                      DropdownButton<String>(
                        value: _selectedLanguage,
                        items: const [
                          DropdownMenuItem(value: 'en', child: Text('English')),
                          DropdownMenuItem(value: 'zh', child: Text('中文 (Mandarin)')),
                          DropdownMenuItem(value: 'es', child: Text('Español')),
                          DropdownMenuItem(value: 'hi', child: Text('हिन्दी')),
                          DropdownMenuItem(value: 'ar', child: Text('العربية')),
                        ],
                        onChanged: (v) {
                          if (v == null) return;
                          setState(() {
                            _selectedLanguage = v;
                          });
                          // Persist selection to app state provider so it survives restarts
                          try {
                            Provider.of<AppStateProvider>(context, listen: false).setLanguage(v);
                          } catch (_) {}
                          widget.onLanguageChanged(v);
                        },
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
          TextField(
                    controller: _emailController,
                    decoration: InputDecoration(
            labelText: I18n.t('email', _selectedLanguage),
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                      prefixIcon: const Icon(Icons.email_outlined),
                    ),
                    keyboardType: TextInputType.emailAddress,
                  ),
                  const SizedBox(height: 12),

                  // Password field
          TextField(
                    controller: _passwordController,
                    obscureText: _obscure,
                    decoration: InputDecoration(
            labelText: I18n.t('password', _selectedLanguage),
                      border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
                      prefixIcon: const Icon(Icons.lock_outline),
                      suffixIcon: IconButton(
                        icon: Icon(_obscure ? Icons.visibility : Icons.visibility_off),
                        onPressed: () => setState(() => _obscure = !_obscure),
                      ),
                    ),
                  ),

                  const SizedBox(height: 18),

                  // Local login submit
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton(
                      child: Text(I18n.t('sign_in', _selectedLanguage)),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.blueAccent,
                        padding: const EdgeInsets.symmetric(vertical: 14),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                      ),
                      onPressed: widget.isLoading
                          ? null
                          : () => widget.onLocalLogin(_emailController.text.trim(), _passwordController.text),
                    ),
                  ),

                  const SizedBox(height: 10),

                  Center(child: Text(I18n.t('or', _selectedLanguage), style: theme.textTheme.bodySmall)),

                  const SizedBox(height: 10),

                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton.icon(
                      icon: const Icon(Icons.login),
                      label: Text(I18n.t('sso', _selectedLanguage)),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.blueAccent,
                        padding: const EdgeInsets.symmetric(vertical: 14),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                      ),
                      onPressed: widget.isLoading ? null : widget.onKeycloak,
                    ),
                  ),

                  const SizedBox(height: 8),
                  // Individual provider buttons
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: [
                      ElevatedButton.icon(
                        icon: const Icon(Icons.email),
                        label: const Text('Google'),
                        onPressed: widget.isLoading ? null : widget.onGoogle,
                        style: ElevatedButton.styleFrom(backgroundColor: Colors.redAccent),
                      ),
                      ElevatedButton.icon(
                        icon: const Icon(Icons.account_box),
                        label: const Text('Microsoft'),
                        onPressed: widget.isLoading ? null : widget.onMicrosoft,
                        style: ElevatedButton.styleFrom(backgroundColor: Colors.blueAccent),
                      ),
                      ElevatedButton.icon(
                        icon: const Icon(Icons.apple),
                        label: const Text('Sign in with Apple'),
                        onPressed: widget.isLoading ? null : widget.onApple,
                        style: ElevatedButton.styleFrom(backgroundColor: Colors.black),
                      ),
                    ],
                  ),

                  const SizedBox(height: 10),

                  SizedBox(
                    width: double.infinity,
                    child: OutlinedButton(
                      onPressed: widget.isLoading ? null : widget.onGuest,
                      style: OutlinedButton.styleFrom(
                        padding: const EdgeInsets.symmetric(vertical: 14),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                      ),
                      child: Text(I18n.t('guest', _selectedLanguage)),
                    ),
                  ),

                  const SizedBox(height: 12),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      TextButton(onPressed: widget.onSignUp, child: Text(I18n.t('sign_up', _selectedLanguage))),
                      TextButton(onPressed: () {}, child: Text(I18n.t('forgot', _selectedLanguage))),
                    ],
                  ),

                  if (widget.resultText.isNotEmpty) ...[
                    const SizedBox(height: 8),
                    Text(widget.resultText, style: const TextStyle(color: Colors.red)),
                  ],
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
