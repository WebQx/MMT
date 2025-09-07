import 'package:flutter/material.dart';

/// A composable login card used by the main app. It mirrors a modern, centered
/// sign-in page with email/password fields, OAuth sign-in button, guest CTA,
/// and helpful links (Sign up / Forgot password).
class LoginCard extends StatefulWidget {
  final VoidCallback onKeycloak;
  final VoidCallback onGuest;
  final void Function(String email, String password) onLocalLogin;
  final VoidCallback? onBack;
  final String resultText;
  final bool isLoading;

  const LoginCard({
    super.key,
    required this.onKeycloak,
    required this.onGuest,
    required this.onLocalLogin,
    this.onBack,
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
                      Text('MMT Health', style: theme.textTheme.headline6?.copyWith(fontWeight: FontWeight.bold)),
                    ],
                  ),
                  const SizedBox(height: 20),

                  // Email field
                  TextField(
                    controller: _emailController,
                    decoration: InputDecoration(
                      labelText: 'Email',
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
                      labelText: 'Password',
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
                      child: const Text('Sign in with email'),
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

                  Center(child: Text('or', style: theme.textTheme.bodySmall)),

                  const SizedBox(height: 10),

                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton.icon(
                      icon: const Icon(Icons.login),
                      label: const Text('Sign in with SSO'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.blueAccent,
                        padding: const EdgeInsets.symmetric(vertical: 14),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                      ),
                      onPressed: widget.isLoading ? null : widget.onKeycloak,
                    ),
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
                      child: const Text('Continue as Guest'),
                    ),
                  ),

                  const SizedBox(height: 12),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      TextButton(onPressed: () {}, child: const Text('Sign Up')),
                      TextButton(onPressed: () {}, child: const Text('Forgot Password?')),
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
