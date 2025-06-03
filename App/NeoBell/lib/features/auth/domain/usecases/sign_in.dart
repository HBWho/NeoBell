import 'package:fpdart/fpdart.dart';

import '../../../../core/error/failure.dart';
import '../../../../core/usecase/usecase.dart';
import '../entities/auth_user.dart';
import '../repositories/auth_repository.dart';

class SignInParams {
  final String username;
  final String password;

  const SignInParams({
    required this.username,
    required this.password,
  });
}

class SignIn implements UseCase<AuthUser, SignInParams> {
  final AuthRepository _repository;

  SignIn(this._repository);

  @override
  Future<Either<Failure, AuthUser>> call(SignInParams params) {
    return _repository.signIn(
      username: params.username,
      password: params.password,
    );
  }
}
