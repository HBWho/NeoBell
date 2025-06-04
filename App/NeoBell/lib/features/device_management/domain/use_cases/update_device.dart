import 'package:fpdart/fpdart.dart';
import '../../../../core/error/failure.dart';
import '../../../../core/usecase/usecase.dart';
import '../entities/device.dart';
import '../repositories/device_repository.dart';

class UpdateDevice implements UseCase<Device, UpdateDeviceParams> {
  final DeviceRepository repository;

  UpdateDevice(this.repository);

  @override
  Future<Either<Failure, Device>> call(UpdateDeviceParams params) async {
    return await repository.updateDevice(
      params.sbcId,
      params.deviceFriendlyName,
    );
  }
}

class UpdateDeviceParams {
  final String sbcId;
  final String deviceFriendlyName;

  UpdateDeviceParams({required this.sbcId, required this.deviceFriendlyName});
}
