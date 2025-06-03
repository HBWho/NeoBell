import 'package:fpdart/fpdart.dart';
import '../../../../core/error/failure.dart';
import '../entities/device.dart';

abstract class DeviceRepository {
  Future<Either<Failure, List<Device>>> getDevices();
  Future<Either<Failure, Device>> getDeviceDetails(String sbcId);
  Future<Either<Failure, Device>> updateDeviceDetails(
      String sbcId, String newName);
  Future<Either<Failure, Unit>> deleteDevice(String sbcId);
  Future<Either<Failure, List<DeviceUser>>> getDeviceUsers(String sbcId);
  Future<Either<Failure, DeviceUser>> addDeviceUser(
      String sbcId, String email, String role);
  Future<Either<Failure, Unit>> removeDeviceUser(String sbcId, String userId);
}

class DeviceUser {
  final String userId;
  final String email;
  final String name;
  final String role;
  final DateTime accessGrantedAt;

  const DeviceUser({
    required this.userId,
    required this.email,
    required this.name,
    required this.role,
    required this.accessGrantedAt,
  });
}
