import '../domain/repositories/token_repository.dart';
import '../error/auth_exception.dart';
import '../error/server_exception.dart';

abstract class TokenManager {
  Future<String> getValidToken();
  Future<void> clearToken();
  Future<String> refreshToken();
}

class TokenManagerImpl implements TokenManager {
  final TokenRepository _tokenRepository;

  TokenManagerImpl({required TokenRepository tokenRepository})
    : _tokenRepository = tokenRepository;

  @override
  Future<String> getValidToken() async {
    try {
      final token = await _tokenRepository.getToken();
      if (token == null) throw AuthException(message: 'No valid token found');
      return token;
    } catch (e) {
      throw AuthException(
        message: 'Failed to get valid token: ${e.toString()}',
      );
    }
  }

  @override
  Future<void> clearToken() async {
    await _tokenRepository.removeToken();
  }

  @override
  Future<String> refreshToken() async {
    try {
      final newToken = await _tokenRepository.refreshToken();
      if (newToken != null) return newToken;
      throw AuthException(message: 'Failed to refresh token: null response');
    } catch (e) {
      throw ServerException('Failed to refresh token: ${e.toString()}');
    }
  }
}
