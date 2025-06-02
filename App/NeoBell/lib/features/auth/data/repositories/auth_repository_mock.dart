import 'package:fpdart/fpdart.dart';

import '../../../../core/constants/constants.dart';
import '../../../../core/error/failure.dart';
import '../../../../core/common/entities/user.dart';
import '../../../../core/error/server_exception.dart';
import '../../domain/repositories/auth_repository.dart';
import '../source/auth_remote_data_source.dart';

class AuthRepositoryImplMock implements AuthRepository {
  final AuthRemoteDataSource _remoteDataSource;

  AuthRepositoryImplMock(this._remoteDataSource);

  @override
  Future<Either<Failure, User>> login({
    required String username,
    required String password,
    required String firebaseToken,
  }) async {
    try {
      return right(User(
        userName: username,
        password: password,
        email: 'aaa',
        name: 'Alexei',
        jwtToken: '',
        roles: [UserRoles.admin],
      ));
    } on ServerException catch (e) {
      return left(Failure(e.message));
    }
  }

  @override
  Future<Either<Failure, Unit>> logout({required String jwtToken}) async {
    try {
      return right(unit);
    } on ServerException catch (e) {
      return left(Failure(e.message));
    }
  }

  @override
  Future<Either<Failure, User>> getUser({required String jwtToken}) async {
    try {
      return right(User(
        userName: 'testuser',
        password: 'password',
        email: 'testuser@example.com',
        name: 'Test User',
        jwtToken: jwtToken,
        roles: [UserRoles.admin],
      ));
    } on ServerException catch (e) {
      return left(Failure(e.message));
    }
  }
}
