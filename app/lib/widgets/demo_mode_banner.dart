import 'package:flutter/material.dart';

/// Simple top banner indicating the app is connected to a demo backend.
/// You can toggle this by providing a runtime flag in the future; for now
/// it is controlled via a compile-time bool (Constants.allowOfflineAuth && kDebugMode).
class DemoModeBanner extends StatelessWidget implements PreferredSizeWidget {
  final bool demoMode;
  final VoidCallback? onUpgrade;
  const DemoModeBanner({super.key, required this.demoMode, this.onUpgrade});

  @override
  Widget build(BuildContext context) {
    if (!demoMode) return const SizedBox.shrink();
    return Material(
      color: Colors.blue.shade600,
      child: SafeArea(
        bottom: false,
        child: Container(
          height: preferredSize.height,
          padding: const EdgeInsets.symmetric(horizontal: 12),
          child: Row(
            children: [
              const Icon(Icons.info_outline, color: Colors.white, size: 16),
              const SizedBox(width: 8),
              const Expanded(
                child: Text(
                  'Demo Mode – limited persistence & features',
                  style: TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.w600),
                  overflow: TextOverflow.ellipsis,
                ),
              ),
              if (onUpgrade != null)
                TextButton(
                  onPressed: onUpgrade,
                  style: TextButton.styleFrom(foregroundColor: Colors.white),
                  child: const Text('UPGRADE'),
                ),
            ],
          ),
        ),
      ),
    );
  }

  @override
  Size get preferredSize => const Size.fromHeight(30);
}
