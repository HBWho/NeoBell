import 'package:fpdart/fpdart.dart';
import '../../../../core/error/failure.dart';
import '../../../../core/usecase/usecase.dart';
import '../entities/device.dart';
import '../repositories/device_repository.dart';

class GetDevices implements UseCase<List<Device>, GetDevicesParams> {
  final DeviceRepository repository;

  GetDevices(this.repository);

  @override
  Future<Either<Failure, List<Device>>> call(GetDevicesParams params) async {
    return await repository.getDevices(
      limit: params.limit,
      lastEvaluatedKey: params.lastEvaluatedKey,
    );
  }
}

class GetDevicesParams {
  final int? limit;
  final String? lastEvaluatedKey;

  GetDevicesParams({this.limit, this.lastEvaluatedKey});
}
