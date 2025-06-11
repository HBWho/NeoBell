import 'package:shared_preferences/shared_preferences.dart';
import 'package:logger/logger.dart';

class BiometricPreferencesService {
  static const String _biometricEnabledKey = 'biometric_enabled';
  static const String _biometricSkippedKey = 'biometric_skipped';

  final Logger _logger = Logger();

  /// Check if biometric authentication is enabled by user
  Future<bool> isBiometricEnabled() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      return prefs.getBool(_biometricEnabledKey) ?? true; // Default to enabled
    } catch (e) {
      _logger.e('Error checking biometric enabled status: $e');
      return true; // Default to enabled on error
    }
  }

  /// Set biometric authentication preference
  Future<void> setBiometricEnabled(bool enabled) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setBool(_biometricEnabledKey, enabled);
      _logger.i('Biometric preference set to: $enabled');
    } catch (e) {
      _logger.e('Error setting biometric preference: $e');
    }
  }

  /// Check if user has skipped biometric setup
  Future<bool> hasBiometricBeenSkipped() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      return prefs.getBool(_biometricSkippedKey) ?? false;
    } catch (e) {
      _logger.e('Error checking biometric skipped status: $e');
      return false;
    }
  }

  /// Mark biometric as skipped by user
  Future<void> setBiometricSkipped(bool skipped) async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setBool(_biometricSkippedKey, skipped);
      _logger.i('Biometric skipped status set to: $skipped');
    } catch (e) {
      _logger.e('Error setting biometric skipped status: $e');
    }
  }

  /// Clear all biometric preferences (useful for logout)
  Future<void> clearBiometricPreferences() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.remove(_biometricEnabledKey);
      await prefs.remove(_biometricSkippedKey);
      _logger.i('Biometric preferences cleared');
    } catch (e) {
      _logger.e('Error clearing biometric preferences: $e');
    }
  }
}
