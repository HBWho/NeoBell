import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../../domain/repositories/config_repository.dart';

part 'settings_state.dart';

class SettingsCubit extends Cubit<SettingsState> {
  SettingsCubit(this._configRepository) : super(SettingsInitial());

  final ConfigRepository _configRepository;

  Future<void> loadSettings() async {
    final apiUrl = await _configRepository.getApiUrl();
    emit(SettingsLoaded(apiUrl: apiUrl));
  }

  Future<void> saveSettings({
    required String apiUrl,
  }) async {
    await _configRepository.setApiUrl(apiUrl);
    emit(SettingsSaved());
  }
}
