abstract interface class TokenRepository {
  Future<String?> getToken();
  Future<void> removeToken();
  Future<String?> refreshToken();
}
