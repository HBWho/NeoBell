import 'package:fpdart/fpdart.dart';
import '../../../../core/error/failure.dart';
import '../../../../core/usecase/usecase.dart';
import '../entities/device.dart';
import '../repositories/device_repository.dart';

class GetDeviceDetails implements UseCase<Device, GetDeviceDetailsParams> {
  final DeviceRepository repository;

  GetDeviceDetails(this.repository);

  @override
  Future<Either<Failure, Device>> call(GetDeviceDetailsParams params) async {
    return await repository.getDeviceDetails(params.sbcId);
  }
}

class GetDeviceDetailsParams {
  final String sbcId;

  GetDeviceDetailsParams({required this.sbcId});
}
