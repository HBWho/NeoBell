part of 'settings_cubit.dart';

@immutable
sealed class SettingsState {}

final class SettingsInitial extends SettingsState {}

final class SettingsLoaded extends SettingsState {
  final String apiUrl;

  SettingsLoaded({
    required this.apiUrl,
  });
}

final class SettingsPasswordLoaded extends SettingsState {
  final bool savePassword;

  SettingsPasswordLoaded({
    required this.savePassword,
  });
}

final class SettingsSaved extends SettingsState {}
