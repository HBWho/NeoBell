import 'package:fpdart/fpdart.dart';
import '../../../../core/error/failure.dart';
import '../../../../core/usecase/usecase.dart';
import '../repositories/device_repository.dart';

class DeleteDevice implements UseCase<Unit, DeleteDeviceParams> {
  final DeviceRepository repository;

  DeleteDevice(this.repository);

  @override
  Future<Either<Failure, Unit>> call(DeleteDeviceParams params) async {
    return await repository.deleteDevice(params.sbcId);
  }
}

class DeleteDeviceParams {
  final String sbcId;

  DeleteDeviceParams({required this.sbcId});
}
