abstract interface class ConfigRepository {
  Future<String> getApiUrl();
  Future<void> setApiUrl(String url);
}
