import 'package:fpdart/fpdart.dart';
import '../../../../core/error/failure.dart';
import '../../../../core/usecase/usecase.dart';
import '../repositories/auth_repository.dart';
import '../../../../core/common/entities/user.dart';

class UserLogout implements UseCase<Unit, User> {
  final AuthRepository repository;
  UserLogout(this.repository);

  @override
  Future<Either<Failure, Unit>> call(User user) async {
    return await repository.logout(jwtToken: user.jwtToken);
  }
}
