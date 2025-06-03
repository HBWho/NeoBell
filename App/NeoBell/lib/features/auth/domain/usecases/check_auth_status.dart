import 'package:fpdart/fpdart.dart';

import '../../../../core/error/failure.dart';
import '../../../../core/usecase/usecase.dart';
import '../entities/auth_user.dart';
import '../repositories/auth_repository.dart';

class CheckAuthStatus implements UseCase<AuthUser?, NoParams> {
  final AuthRepository _repository;

  CheckAuthStatus(this._repository);

  @override
  Future<Either<Failure, AuthUser?>> call(NoParams params) async {
    final isSignedInResult = await _repository.isSignedIn();

    return isSignedInResult.fold(
      (failure) => left(failure),
      (isSignedIn) async {
        if (!isSignedIn) {
          return right(null);
        }
        final userResult = await _repository.getCurrentUser();
        return userResult;
      },
    );
  }
}
