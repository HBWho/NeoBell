import 'package:amplify_auth_cognito/amplify_auth_cognito.dart' as amplify;
import 'package:amplify_flutter/amplify_flutter.dart' as aws;
import 'package:fpdart/fpdart.dart';
import 'package:logger/logger.dart';

import '../../../../core/error/failure.dart';
import '../../domain/entities/auth_user.dart';
import '../../domain/repositories/auth_repository.dart';
import '../mappers/auth_user_mapper.dart';

class CognitoAuthRepository implements AuthRepository {
  final Logger _logger = Logger();

  @override
  Future<Either<Failure, AuthUser>> signUp({
    required String username,
    required String password,
    required String email,
  }) async {
    try {
      final result = await aws.Amplify.Auth.signUp(
        username: username,
        password: password,
        options: amplify.SignUpOptions(
          userAttributes: {amplify.CognitoUserAttributeKey.email: email},
        ),
      );

      if (result.isSignUpComplete) {
        final attributes = [
          amplify.AuthUserAttribute(
            userAttributeKey: amplify.CognitoUserAttributeKey.sub,
            value: username,
          ),
          amplify.AuthUserAttribute(
            userAttributeKey: amplify.CognitoUserAttributeKey.email,
            value: email,
          ),
        ];

        return right(AuthUserMapper.fromCognitoAttributes(attributes));
      }

      return left(Failure('Sign up is not complete'));
    } on aws.AuthException catch (e) {
      _logger.e('Sign up failed: ${e.message}');
      return left(Failure(e.message));
    }
  }

  @override
  Future<Either<Failure, AuthUser>> confirmSignUp({
    required String username,
    required String confirmationCode,
  }) async {
    try {
      final result = await aws.Amplify.Auth.confirmSignUp(
        username: username,
        confirmationCode: confirmationCode,
      );

      if (result.isSignUpComplete) {
        final attributes = [
          amplify.AuthUserAttribute(
            userAttributeKey: amplify.CognitoUserAttributeKey.sub,
            value: username,
          ),
        ];

        return right(AuthUserMapper.fromCognitoAttributes(attributes));
      }

      return left(Failure('Sign up confirmation failed'));
    } on aws.AuthException catch (e) {
      _logger.e('Sign up confirmation failed: ${e.message}');
      return left(Failure(e.message));
    }
  }

  @override
  Future<Either<Failure, AuthUser>> signIn({
    required String username,
    required String password,
  }) async {
    try {
      final result = await aws.Amplify.Auth.signIn(
        username: username,
        password: password,
      );

      if (result.isSignedIn) {
        final attributes = await aws.Amplify.Auth.fetchUserAttributes();
        return right(AuthUserMapper.fromCognitoAttributes(attributes));
      }

      return left(Failure('Sign in failed'));
    } on aws.AuthException catch (e) {
      _logger.e('Sign in failed: ${e.message}');
      return left(Failure(e.message));
    }
  }

  @override
  Future<Either<Failure, Unit>> signOut() async {
    try {
      await aws.Amplify.Auth.signOut();
      return right(unit);
    } on aws.AuthException catch (e) {
      _logger.e('Sign out failed: ${e.message}');
      return left(Failure(e.message));
    }
  }

  @override
  Future<Either<Failure, Unit>> resetPassword({
    required String username,
  }) async {
    try {
      await aws.Amplify.Auth.resetPassword(username: username);
      return right(unit);
    } on aws.AuthException catch (e) {
      _logger.e('Reset password failed: ${e.message}');
      return left(Failure(e.message));
    }
  }

  @override
  Future<Either<Failure, Unit>> confirmResetPassword({
    required String username,
    required String newPassword,
    required String confirmationCode,
  }) async {
    try {
      await aws.Amplify.Auth.confirmResetPassword(
        username: username,
        newPassword: newPassword,
        confirmationCode: confirmationCode,
      );
      return right(unit);
    } on aws.AuthException catch (e) {
      _logger.e('Confirm reset password failed: ${e.message}');
      return left(Failure(e.message));
    }
  }

  @override
  Future<Either<Failure, AuthUser>> getCurrentUser() async {
    try {
      final attributes = await aws.Amplify.Auth.fetchUserAttributes();
      return right(AuthUserMapper.fromCognitoAttributes(attributes));
    } on aws.AuthException catch (e) {
      _logger.e('Get current user failed: ${e.message}');
      return left(Failure(e.message));
    }
  }

  @override
  Future<Either<Failure, bool>> isSignedIn() async {
    try {
      final session = await aws.Amplify.Auth.fetchAuthSession();
      return right(session.isSignedIn);
    } on aws.AuthException catch (e) {
      _logger.e('Check signed in state failed: ${e.message}');
      return left(Failure(e.message));
    }
  }

  @override
  Future<Either<Failure, Unit>> updatePassword({
    required String oldPassword,
    required String newPassword,
  }) async {
    try {
      await aws.Amplify.Auth.updatePassword(
        oldPassword: oldPassword,
        newPassword: newPassword,
      );
      _logger.i('Password updated successfully');
      return right(unit);
    } on aws.AuthException catch (e) {
      _logger.e('Update password failed: ${e.message}');
      return left(Failure(e.message));
    }
  }
}
