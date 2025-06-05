import 'package:fpdart/fpdart.dart';

import '../../../../core/error/failure.dart';
import '../../../../core/usecase/usecase.dart';
import '../repositories/auth_repository.dart';

class UpdatePasswordParams {
  final String oldPassword;
  final String newPassword;

  const UpdatePasswordParams({
    required this.oldPassword,
    required this.newPassword,
  });
}

class UpdatePassword implements UseCase<Unit, UpdatePasswordParams> {
  final AuthRepository _repository;

  UpdatePassword(this._repository);

  @override
  Future<Either<Failure, Unit>> call(UpdatePasswordParams params) {
    return _repository.updatePassword(
      oldPassword: params.oldPassword,
      newPassword: params.newPassword,
    );
  }
}
