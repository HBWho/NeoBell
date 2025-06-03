import 'package:fpdart/fpdart.dart';

import '../../../../core/error/failure.dart';
import '../../../../core/usecase/usecase.dart';
import '../entities/user_profile.dart';
import '../repositories/user_profile_repository.dart';

class GetCurrentProfile implements UseCase<UserProfile, NoParams> {
  final UserProfileRepository repository;

  GetCurrentProfile(this.repository);

  @override
  Future<Either<Failure, UserProfile>> call(NoParams params) async {
    return await repository.getCurrentProfile();
  }
}
