import 'package:fpdart/fpdart.dart';
import '../../../../core/error/failure.dart';
import '../../../../core/usecase/usecase.dart';
import '../repositories/device_repository.dart';

class AddDeviceUserParams {
  final String sbcId;
  final String email;
  final String role;

  AddDeviceUserParams({
    required this.sbcId,
    required this.email,
    required this.role,
  });
}

class AddDeviceUser implements UseCase<DeviceUser, AddDeviceUserParams> {
  final DeviceRepository repository;

  AddDeviceUser(this.repository);

  @override
  Future<Either<Failure, DeviceUser>> call(AddDeviceUserParams params) async {
    return await repository.addDeviceUser(
      params.sbcId,
      params.email,
      params.role,
    );
  }
}
