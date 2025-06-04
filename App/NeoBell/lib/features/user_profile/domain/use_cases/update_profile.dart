import 'package:fpdart/fpdart.dart';

import '../../../../core/error/failure.dart';
import '../../../../core/usecase/usecase.dart';
import '../entities/user_profile.dart';
import '../repositories/user_profile_repository.dart';

class UpdateProfileParams {
  final String name;

  const UpdateProfileParams({required this.name});
}

class UpdateProfile implements UseCase<UserProfile, UpdateProfileParams> {
  final UserProfileRepository repository;

  const UpdateProfile(this.repository);

  @override
  Future<Either<Failure, UserProfile>> call(UpdateProfileParams params) async {
    return await repository.updateProfile(name: params.name);
  }
}
