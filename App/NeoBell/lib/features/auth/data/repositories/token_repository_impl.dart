import 'package:amplify_auth_cognito/amplify_auth_cognito.dart';
import 'package:amplify_flutter/amplify_flutter.dart';
import 'package:logger/logger.dart';

import '../../../../core/domain/repositories/token_repository.dart';
import '../../../../core/error/server_exception.dart';
import '../../../../core/error/auth_exception.dart' as app_auth;

class TokenRepositoryImpl implements TokenRepository {
  final Logger _logger = Logger();

  TokenRepositoryImpl();

  @override
  Future<String?> getToken() async {
    try {
      final authSession = await Amplify.Auth.fetchAuthSession();
      if (authSession is CognitoAuthSession && authSession.isSignedIn) {
        final cognitoPoolToken = authSession.userPoolTokensResult.valueOrNull;
        return cognitoPoolToken?.idToken.raw;
      }
      _logger.w(
          'TokenRepositoryImpl: No active Amplify session or user not signed in.');
      return null;
    } catch (e) {
      _logger.e('TokenRepositoryImpl: Error fetching Amplify session: $e');
      if (e is SignedOutException || e is SessionExpiredException) {
        throw app_auth.AuthException(
            message: 'User is signed out or session expired.');
      }
      throw ServerException('Failed to fetch token from Amplify: $e');
    }
  }

  @override
  Future<void> removeToken() async {
    try {
      await Amplify.Auth.signOut();
    } catch (e) {
      _logger.e('TokenRepositoryImpl: Error while signing out: $e');
    }
  }

  @override
  Future<String?> refreshToken() async {
    try {
      _logger
          .i('TokenRepositoryImpl: Attempting to refresh token via Amplify.');
      final authSession = await Amplify.Auth.fetchAuthSession(
        options: FetchAuthSessionOptions(forceRefresh: true),
      );
      if (authSession is CognitoAuthSession && authSession.isSignedIn) {
        final cognitoPoolToken = authSession.userPoolTokensResult.valueOrNull;
        _logger.i('TokenRepositoryImpl: Token refresh successful.');
        return cognitoPoolToken?.idToken.raw;
      }
      _logger.w(
          'TokenRepositoryImpl: Refresh attempt did not result in a signed-in session.');
      throw app_auth.AuthException(
          message: 'Failed to refresh token or session is invalid.');
    } on SessionExpiredException catch (e) {
      _logger.e('TokenRepositoryImpl: Session expired and refresh failed: $e');
      throw app_auth.AuthException(
          message: 'Session expired, please log in again.');
    } catch (e) {
      _logger.e('TokenRepositoryImpl: Error during token refresh: $e');
      throw ServerException('Failed to refresh token: $e');
    }
  }
}
