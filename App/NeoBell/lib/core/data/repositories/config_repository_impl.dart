import '../../domain/repositories/config_repository.dart';
import '../../constants/constants.dart';
import '../../constants/api_constants.dart';
import '../../domain/repositories/local_storage_repository.dart';

class ConfigRepositoryImpl implements ConfigRepository {
  final LocalStorageRepository _nonSecureStorage;

  ConfigRepositoryImpl({
    required LocalStorageRepository nonSecureStorage,
  }) : _nonSecureStorage = nonSecureStorage;

  @override
  Future<String> getApiUrl() async {
    return await _nonSecureStorage.readData(DataKeys.apiUrl.name) ??
        ApiConstants.defaultUrl;
  }

  @override
  Future<void> setApiUrl(String url) async {
    await _nonSecureStorage.writeData(DataKeys.apiUrl.name, url);
  }
}
