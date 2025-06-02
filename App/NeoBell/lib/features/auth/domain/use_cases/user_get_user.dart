import 'package:fpdart/fpdart.dart';
import '../../../../core/error/failure.dart';
import '../../../../core/common/entities/user.dart';
import '../../../../core/usecase/usecase.dart';
import '../repositories/auth_repository.dart';

class UserGetUser implements UseCase<User, String> {
  final AuthRepository repository;
  UserGetUser(this.repository);

  @override
  Future<Either<Failure, User>> call(String params) async {
    return await repository.getUser(jwtToken: params);
  }
}
