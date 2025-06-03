import 'package:fpdart/fpdart.dart';
import '../../../../core/error/failure.dart';
import '../../../../core/usecase/usecase.dart';
import '../repositories/device_repository.dart';

class GetDeviceUsers implements UseCase<List<DeviceUser>, String> {
  final DeviceRepository repository;

  GetDeviceUsers(this.repository);

  @override
  Future<Either<Failure, List<DeviceUser>>> call(String sbcId) async {
    return await repository.getDeviceUsers(sbcId);
  }
}
