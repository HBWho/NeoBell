import 'package:fpdart/fpdart.dart';
import '../../../../core/error/failure.dart';
import '../../../../core/usecase/usecase.dart';
import '../entities/device.dart';
import '../repositories/device_repository.dart';

class GetDeviceDetails implements UseCase<Device, String> {
  final DeviceRepository repository;

  GetDeviceDetails(this.repository);

  @override
  Future<Either<Failure, Device>> call(String sbcId) async {
    return await repository.getDeviceDetails(sbcId);
  }
}
