import 'package:local_auth/local_auth.dart';
import 'package:local_auth_android/local_auth_android.dart';
import 'package:logger/logger.dart';

class BiometricService {
  final LocalAuthentication _localAuth = LocalAuthentication();
  final Logger _logger = Logger();

  /// Check if biometric authentication is available on the device
  Future<bool> isBiometricAvailable() async {
    try {
      final bool isAvailable = await _localAuth.isDeviceSupported();
      final bool hasEnrolledBiometrics = await _localAuth.canCheckBiometrics;

      _logger.i('Device supports biometrics: $isAvailable');
      _logger.i('Has enrolled biometrics: $hasEnrolledBiometrics');

      return isAvailable && hasEnrolledBiometrics;
    } catch (e) {
      _logger.e('Error checking biometric availability: $e');
      return false;
    }
  }

  /// Get available biometric types on the device
  Future<List<BiometricType>> getAvailableBiometrics() async {
    try {
      return await _localAuth.getAvailableBiometrics();
    } catch (e) {
      _logger.e('Error getting available biometrics: $e');
      return [];
    }
  }

  /// Authenticate using biometrics
  Future<BiometricAuthResult> authenticateWithBiometrics({
    String localizedReason = 'Autenticar para acessar o NeoBell',
  }) async {
    try {
      // Check if biometrics are available
      final bool isAvailable = await isBiometricAvailable();
      if (!isAvailable) {
        return BiometricAuthResult.notAvailable;
      }

      // Perform biometric authentication
      final bool didAuthenticate = await _localAuth.authenticate(
        localizedReason: localizedReason,
        authMessages: const [
          AndroidAuthMessages(
            signInTitle: 'Autenticação Biométrica',
            cancelButton: 'Cancelar',
            deviceCredentialsRequiredTitle: 'Credenciais do Dispositivo',
            deviceCredentialsSetupDescription:
                'Configure a autenticação biométrica nas configurações do dispositivo',
            goToSettingsButton: 'Configurações',
            goToSettingsDescription:
                'Configure a autenticação biométrica nas configurações do dispositivo',
          ),
        ],
        options: const AuthenticationOptions(
          biometricOnly: false,
          stickyAuth: true,
          sensitiveTransaction: true,
        ),
      );

      if (didAuthenticate) {
        _logger.i('Biometric authentication successful');
        return BiometricAuthResult.success;
      } else {
        _logger.w('Biometric authentication failed or was cancelled');
        return BiometricAuthResult.failed;
      }
    } catch (e) {
      _logger.e('Error during biometric authentication: $e');
      if (e.toString().contains('NotAvailable')) {
        return BiometricAuthResult.notAvailable;
      } else if (e.toString().contains('NotEnrolled')) {
        return BiometricAuthResult.notEnrolled;
      }
      return BiometricAuthResult.error;
    }
  }

  /// Check if device supports biometrics (hardware check)
  Future<bool> isDeviceSupported() async {
    try {
      return await _localAuth.isDeviceSupported();
    } catch (e) {
      _logger.e('Error checking device support: $e');
      return false;
    }
  }

  /// Stop authentication (if possible)
  Future<bool> stopAuthentication() async {
    try {
      return await _localAuth.stopAuthentication();
    } catch (e) {
      _logger.e('Error stopping authentication: $e');
      return false;
    }
  }
}

/// Enum representing the result of biometric authentication
enum BiometricAuthResult { success, failed, notAvailable, notEnrolled, error }

/// Extension to provide user-friendly messages for BiometricAuthResult
extension BiometricAuthResultExtension on BiometricAuthResult {
  String get message {
    switch (this) {
      case BiometricAuthResult.success:
        return 'Autenticação bem-sucedida';
      case BiometricAuthResult.failed:
        return 'Falha na autenticação ou cancelada pelo usuário';
      case BiometricAuthResult.notAvailable:
        return 'Autenticação biométrica não disponível neste dispositivo';
      case BiometricAuthResult.notEnrolled:
        return 'Nenhuma biometria cadastrada no dispositivo';
      case BiometricAuthResult.error:
        return 'Erro durante a autenticação biométrica';
    }
  }

  bool get isSuccess => this == BiometricAuthResult.success;
  bool get isFailed => this == BiometricAuthResult.failed;
  bool get isNotAvailable => this == BiometricAuthResult.notAvailable;
  bool get isNotEnrolled => this == BiometricAuthResult.notEnrolled;
  bool get isError => this == BiometricAuthResult.error;
}
