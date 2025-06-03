import 'package:fpdart/fpdart.dart';

import '../../../../core/error/failure.dart';
import '../entities/auth_user.dart';

abstract interface class AuthRepository {
  Future<Either<Failure, AuthUser>> signUp({
    required String username,
    required String password,
    required String email,
  });

  Future<Either<Failure, AuthUser>> confirmSignUp({
    required String username,
    required String confirmationCode,
  });

  Future<Either<Failure, AuthUser>> signIn({
    required String username,
    required String password,
  });

  Future<Either<Failure, Unit>> signOut();

  Future<Either<Failure, Unit>> resetPassword({
    required String username,
  });

  Future<Either<Failure, Unit>> confirmResetPassword({
    required String username,
    required String newPassword,
    required String confirmationCode,
  });

  Future<Either<Failure, AuthUser>> getCurrentUser();

  Future<Either<Failure, bool>> isSignedIn();
}
