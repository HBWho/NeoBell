import 'package:fpdart/fpdart.dart';
import '../../../../core/error/failure.dart';
import '../../../../core/usecase/usecase.dart';
import '../entities/device_user.dart';
import '../repositories/device_repository.dart';

class GetDeviceUsers
    implements UseCase<List<DeviceUser>, GetDeviceUsersParams> {
  final DeviceRepository repository;

  GetDeviceUsers(this.repository);

  @override
  Future<Either<Failure, List<DeviceUser>>> call(
    GetDeviceUsersParams params,
  ) async {
    return await repository.getDeviceUsers(params.sbcId);
  }
}

class GetDeviceUsersParams {
  final String sbcId;

  GetDeviceUsersParams({required this.sbcId});
}
