import 'package:flutter/material.dart';
import 'package:neobell/core/constants/constants.dart';
import 'package:neobell/core/theme/theme.dart';

class SplashScreen extends StatelessWidget {
  const SplashScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      color: AppColors.primary,
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Flexible(
            child: Container(
              constraints: const BoxConstraints(maxWidth: 300, maxHeight: 300),
              child: Image.asset(AssetsConstants.logo, fit: BoxFit.contain),
            ),
          ),
          const SizedBox(height: 40),
          const CircularProgressIndicator(
            valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
          ),
          const SizedBox(height: 20),
          const Text(
            'Authenticating...',
            style: TextStyle(color: AppColors.text, fontSize: 16),
          ),
        ],
      ),
    );
  }
}
