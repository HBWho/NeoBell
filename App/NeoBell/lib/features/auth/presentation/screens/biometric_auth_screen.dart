import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../../../core/constants/constants.dart';
import '../../../../core/services/biometric_service.dart';
import '../../../../core/theme/theme.dart';
import '../../../../core/utils/show_snackbar.dart';
import '../cubit/auth_cubit.dart';

class BiometricAuthScreen extends StatefulWidget {
  const BiometricAuthScreen({super.key});

  @override
  State<BiometricAuthScreen> createState() => _BiometricAuthScreenState();
}

class _BiometricAuthScreenState extends State<BiometricAuthScreen>
    with TickerProviderStateMixin {
  final BiometricService _biometricService = BiometricService();
  late AnimationController _pulseController;
  late AnimationController _shakeController;
  late Animation<double> _pulseAnimation;
  late Animation<double> _shakeAnimation;

  bool _isAuthenticating = false;
  bool _hasError = false;

  @override
  void initState() {
    super.initState();
    _setupAnimations();
    _checkBiometricAvailabilityAndAuthenticate();
  }

  void _setupAnimations() {
    // Pulse animation for the fingerprint icon
    _pulseController = AnimationController(
      duration: const Duration(seconds: 2),
      vsync: this,
    );
    _pulseAnimation = Tween<double>(begin: 0.8, end: 1.2).animate(
      CurvedAnimation(parent: _pulseController, curve: Curves.easeInOut),
    );

    // Shake animation for error states
    _shakeController = AnimationController(
      duration: const Duration(milliseconds: 500),
      vsync: this,
    );
    _shakeAnimation = Tween<double>(begin: -10.0, end: 10.0).animate(
      CurvedAnimation(parent: _shakeController, curve: Curves.elasticIn),
    );

    _pulseController.repeat(reverse: true);
  }

  @override
  void dispose() {
    _pulseController.dispose();
    _shakeController.dispose();
    super.dispose();
  }

  Future<void> _checkBiometricAvailabilityAndAuthenticate() async {
    final isAvailable = await _biometricService.isBiometricAvailable();

    if (!isAvailable) {
      if (mounted) {
        _showBiometricNotAvailableDialog();
      }
      return;
    }

    // Automatically start authentication after a short delay
    await Future.delayed(const Duration(milliseconds: 800));
    if (mounted) {
      _performBiometricAuth();
    }
  }

  Future<void> _performBiometricAuth() async {
    if (_isAuthenticating) return;

    setState(() {
      _isAuthenticating = true;
      _hasError = false;
    });

    try {
      final result = await _biometricService.authenticateWithBiometrics(
        localizedReason: 'Confirm your identity to access the app',
      );

      if (!mounted) return;

      switch (result) {
        case BiometricAuthResult.success:
          _handleAuthSuccess();
          break;
        case BiometricAuthResult.failed:
          _handleAuthFailure('Authentication canceled or failed');
          break;
        case BiometricAuthResult.notAvailable:
          _showBiometricNotAvailableDialog();
          break;
        case BiometricAuthResult.notEnrolled:
          _showBiometricNotEnrolledDialog();
          break;
        case BiometricAuthResult.error:
          _handleAuthFailure('Error during biometric authentication');
          break;
      }
    } catch (e) {
      if (mounted) {
        _handleAuthFailure('Unexpected error: $e');
      }
    } finally {
      if (mounted) {
        setState(() {
          _isAuthenticating = false;
        });
      }
    }
  }

  void _handleAuthSuccess() {
    context.read<AuthCubit>().completeBiometricAuth();
  }

  void _handleAuthFailure(String message) {
    setState(() {
      _hasError = true;
    });

    _shakeController.forward().then((_) {
      _shakeController.reverse();
    });

    showSnackBar(context, message: message, isError: true);
  }

  void _showBiometricNotAvailableDialog() {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder:
          (context) => AlertDialog(
            title: const Text('Biometry Not Available'),
            content: const Text(
              'Biometric authentication is not available on this device. '
              'You will be redirected to log in again.',
            ),
            actions: [
              TextButton(
                onPressed: () {
                  Navigator.of(context).pop();
                  context.read<AuthCubit>().signOut();
                },
                child: const Text('OK'),
              ),
            ],
          ),
    );
  }

  void _showBiometricNotEnrolledDialog() {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder:
          (context) => AlertDialog(
            title: const Text('Biometry Not Enrolled'),
            content: const Text(
              'No biometric authentication is enrolled on this device. '
              'Please enroll in the system settings or log in again.',
            ),
            actions: [
              TextButton(
                onPressed: () {
                  Navigator.of(context).pop();
                  context.read<AuthCubit>().signOut();
                },
                child: const Text('Log In'),
              ),
            ],
          ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.primary,
      body: SafeArea(
        minimum: const EdgeInsets.only(top: 16),
        child: Column(
          children: [
            // App Logo
            ConstrainedBox(
              constraints: BoxConstraints(
                maxHeight: MediaQuery.of(context).size.height * 0.15,
                maxWidth: MediaQuery.of(context).size.width * 0.95,
              ),
              child: Image.asset(AssetsConstants.logo),
            ),
            const SizedBox(height: 10),
            Text(
              'Authentication System',
              style: TextStyle(
                fontSize: 18,
                color: Colors.grey[600],
                fontWeight: FontWeight.w500,
              ),
            ),
            const SizedBox(height: 20),
            Expanded(
              child: Container(
                margin: const EdgeInsets.symmetric(horizontal: 20),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(15),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.grey.withAlpha(
                        Color.getAlphaFromOpacity(0.5),
                      ),
                      spreadRadius: 5,
                      blurRadius: 7,
                      offset: const Offset(0, 3),
                    ),
                  ],
                ),
                child: Padding(
                  padding: const EdgeInsets.all(24.0),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Spacer(),
                      AnimatedBuilder(
                        animation: _pulseAnimation,
                        builder: (context, child) {
                          return AnimatedBuilder(
                            animation: _shakeAnimation,
                            builder: (context, child) {
                              return Transform.translate(
                                offset:
                                    _hasError
                                        ? Offset(_shakeAnimation.value, 0)
                                        : Offset.zero,
                                child: Transform.scale(
                                  scale: _pulseAnimation.value,
                                  child: Container(
                                    width: 120,
                                    height: 120,
                                    decoration: BoxDecoration(
                                      color: AppColors.button.withOpacity(0.1),
                                      shape: BoxShape.circle,
                                      border: Border.all(
                                        color:
                                            _hasError
                                                ? AppColors.red.withOpacity(0.5)
                                                : AppColors.button.withOpacity(
                                                  0.3,
                                                ),
                                        width: 2,
                                      ),
                                    ),
                                    child: Icon(
                                      Icons.fingerprint,
                                      size: 60,
                                      color:
                                          _hasError
                                              ? AppColors.red
                                              : AppColors.button,
                                    ),
                                  ),
                                ),
                              );
                            },
                          );
                        },
                      ),
                      const SizedBox(height: 40),
                      Text(
                        _isAuthenticating
                            ? 'Authenticating...'
                            : _hasError
                            ? 'Try Again'
                            : 'Touch the biometric sensor',
                        style: const TextStyle(
                          color: AppColors.text,
                          fontSize: 18,
                          fontWeight: FontWeight.w500,
                        ),
                        textAlign: TextAlign.center,
                      ),
                      const SizedBox(height: 12),
                      Text(
                        'Use your fingerprint or facial recognition\n to access the app',
                        style: TextStyle(color: Colors.grey[600], fontSize: 14),
                        textAlign: TextAlign.center,
                      ),
                      const Spacer(),
                      Column(
                        children: [
                          if (_hasError && !_isAuthenticating) ...[
                            SizedBox(
                              width: double.infinity,
                              child: ElevatedButton(
                                onPressed: _performBiometricAuth,
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: AppColors.button,
                                  foregroundColor: AppColors.buttonText,
                                  padding: const EdgeInsets.symmetric(
                                    vertical: 16,
                                  ),
                                  shape: RoundedRectangleBorder(
                                    borderRadius: BorderRadius.circular(8),
                                  ),
                                ),
                                child: const Text(
                                  'Try Again',
                                  style: TextStyle(
                                    fontSize: 16,
                                    fontWeight: FontWeight.w600,
                                  ),
                                ),
                              ),
                            ),
                            const SizedBox(height: 12),
                          ],
                          SizedBox(
                            width: double.infinity,
                            child: TextButton(
                              onPressed: () {
                                context.read<AuthCubit>().signOut();
                              },
                              style: TextButton.styleFrom(
                                foregroundColor: AppColors.text,
                                padding: const EdgeInsets.symmetric(
                                  vertical: 16,
                                ),
                              ),
                              child: const Text(
                                'Log In Again',
                                style: TextStyle(
                                  fontSize: 14,
                                  decoration: TextDecoration.underline,
                                ),
                              ),
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 20),
                    ],
                  ),
                ),
              ),
            ),
            const SizedBox(height: 40),
          ],
        ),
      ),
    );
  }
}
