import 'package:fpdart/fpdart.dart';

import '../../../../core/error/failure.dart';
import '../../../../core/usecase/usecase.dart';
import '../repositories/user_profile_repository.dart';

class UpdateDeviceTokenParams {
  final String deviceToken;

  const UpdateDeviceTokenParams({required this.deviceToken});
}

class UpdateDeviceToken implements UseCase<Unit, UpdateDeviceTokenParams> {
  final UserProfileRepository repository;

  const UpdateDeviceToken(this.repository);

  @override
  Future<Either<Failure, Unit>> call(UpdateDeviceTokenParams params) async {
    return await repository.updateDeviceToken(
      deviceToken: params.deviceToken,
    );
  }
}
