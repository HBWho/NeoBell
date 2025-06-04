import 'package:fpdart/fpdart.dart';
import '../../../../core/error/failure.dart';
import '../entities/device.dart';
import '../entities/device_user.dart';

abstract class DeviceRepository {
  Future<Either<Failure, List<Device>>> getDevices({
    int? limit,
    String? lastEvaluatedKey,
  });

  Future<Either<Failure, Device>> getDeviceDetails(String sbcId);

  Future<Either<Failure, Device>> updateDevice(
    String sbcId,
    String deviceFriendlyName,
  );

  Future<Either<Failure, Unit>> deleteDevice(String sbcId);

  Future<Either<Failure, List<DeviceUser>>> getDeviceUsers(String sbcId);

  Future<Either<Failure, Unit>> addDeviceUser(String sbcId, String userEmail);

  Future<Either<Failure, Unit>> removeDeviceUser(String sbcId, String userId);
}
