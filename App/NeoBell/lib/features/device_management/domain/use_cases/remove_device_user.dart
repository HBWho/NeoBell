import 'package:fpdart/fpdart.dart';
import '../../../../core/error/failure.dart';
import '../../../../core/usecase/usecase.dart';
import '../repositories/device_repository.dart';

class RemoveDeviceUser implements UseCase<Unit, RemoveDeviceUserParams> {
  final DeviceRepository repository;

  RemoveDeviceUser(this.repository);

  @override
  Future<Either<Failure, Unit>> call(RemoveDeviceUserParams params) async {
    return await repository.removeDeviceUser(params.sbcId, params.userId);
  }
}

class RemoveDeviceUserParams {
  final String sbcId;
  final String userId;

  RemoveDeviceUserParams({required this.sbcId, required this.userId});
}
