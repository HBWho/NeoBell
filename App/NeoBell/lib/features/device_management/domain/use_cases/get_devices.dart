import 'package:fpdart/fpdart.dart';
import '../../../../core/error/failure.dart';
import '../../../../core/usecase/usecase.dart';
import '../entities/device.dart';
import '../repositories/device_repository.dart';

class GetDevices implements UseCase<List<Device>, NoParams> {
  final DeviceRepository repository;

  GetDevices(this.repository);

  @override
  Future<Either<Failure, List<Device>>> call(NoParams params) async {
    return await repository.getDevices();
  }
}
