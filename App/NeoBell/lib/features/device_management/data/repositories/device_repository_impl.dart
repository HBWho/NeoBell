import 'package:fpdart/fpdart.dart';
import '../../../../core/error/failure.dart';
import '../../../../core/error/server_failure.dart';
import '../../../../core/error/server_exception.dart';
import '../../domain/entities/device.dart';
import '../../domain/repositories/device_repository.dart';
import '../datasources/device_remote_data_source.dart';

class DeviceRepositoryImpl implements DeviceRepository {
  final DeviceRemoteDataSource _remoteDataSource;
  final String _jwtToken;

  DeviceRepositoryImpl({
    required DeviceRemoteDataSource remoteDataSource,
    required String jwtToken,
  })  : _remoteDataSource = remoteDataSource,
        _jwtToken = jwtToken;

  @override
  Future<Either<Failure, List<Device>>> getDevices() async {
    try {
      final devices = await _remoteDataSource.getDevices(_jwtToken);
      return right(devices);
    } on ServerException catch (e) {
      return left(ServerFailure(e.message));
    }
  }

  @override
  Future<Either<Failure, Device>> getDeviceDetails(String sbcId) async {
    try {
      final device = await _remoteDataSource.getDeviceDetails(_jwtToken, sbcId);
      return right(device);
    } on ServerException catch (e) {
      return left(ServerFailure(e.message));
    }
  }

  @override
  Future<Either<Failure, Device>> updateDeviceDetails(
      String sbcId, String newName) async {
    try {
      final device = await _remoteDataSource.updateDeviceDetails(
          _jwtToken, sbcId, newName);
      return right(device);
    } on ServerException catch (e) {
      return left(ServerFailure(e.message));
    }
  }

  @override
  Future<Either<Failure, Unit>> deleteDevice(String sbcId) async {
    try {
      await _remoteDataSource.deleteDevice(_jwtToken, sbcId);
      return right(unit);
    } on ServerException catch (e) {
      return left(ServerFailure(e.message));
    }
  }

  @override
  Future<Either<Failure, List<DeviceUser>>> getDeviceUsers(String sbcId) async {
    try {
      final users = await _remoteDataSource.getDeviceUsers(_jwtToken, sbcId);
      return right(users);
    } on ServerException catch (e) {
      return left(ServerFailure(e.message));
    }
  }

  @override
  Future<Either<Failure, DeviceUser>> addDeviceUser(
      String sbcId, String email, String role) async {
    try {
      final user =
          await _remoteDataSource.addDeviceUser(_jwtToken, sbcId, email, role);
      return right(user);
    } on ServerException catch (e) {
      return left(ServerFailure(e.message));
    }
  }

  @override
  Future<Either<Failure, Unit>> removeDeviceUser(
      String sbcId, String userId) async {
    try {
      await _remoteDataSource.removeDeviceUser(_jwtToken, sbcId, userId);
      return right(unit);
    } on ServerException catch (e) {
      return left(ServerFailure(e.message));
    }
  }
}
