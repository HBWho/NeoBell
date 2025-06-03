import 'package:fpdart/fpdart.dart';
import '../../../../core/error/failure.dart';
import '../../../../core/usecase/usecase.dart';
import '../entities/device.dart';
import '../repositories/device_repository.dart';

class UpdateDeviceParams {
  final String sbcId;
  final String newName;

  UpdateDeviceParams({
    required this.sbcId,
    required this.newName,
  });
}

class UpdateDeviceDetails implements UseCase<Device, UpdateDeviceParams> {
  final DeviceRepository repository;

  UpdateDeviceDetails(this.repository);

  @override
  Future<Either<Failure, Device>> call(UpdateDeviceParams params) async {
    return await repository.updateDeviceDetails(
      params.sbcId,
      params.newName,
    );
  }
}
