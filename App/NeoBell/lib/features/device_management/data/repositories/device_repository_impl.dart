import 'package:fpdart/fpdart.dart';
import '../../../../core/error/failure.dart';
import '../../../../core/error/server_exception.dart';
import '../../../../core/error/server_failure.dart';
import '../../domain/entities/device.dart';
import '../../domain/entities/device_user.dart';
import '../../domain/repositories/device_repository.dart';
import '../datasources/device_remote_data_source.dart';

class DeviceRepositoryImpl implements DeviceRepository {
  final DeviceRemoteDataSource _remoteDataSource;

  DeviceRepositoryImpl(this._remoteDataSource);

  @override
  Future<Either<Failure, List<Device>>> getDevices({
    int? limit,
    String? lastEvaluatedKey,
  }) async {
    try {
      final devices = await _remoteDataSource.getDevices(
        limit: limit,
        lastEvaluatedKey: lastEvaluatedKey,
      );
      return right(devices);
    } on ServerException catch (e) {
      return left(ServerFailure(e.message));
    }
  }

  @override
  Future<Either<Failure, Device>> getDeviceDetails(String sbcId) async {
    try {
      final device = await _remoteDataSource.getDeviceDetails(sbcId);
      return right(device);
    } on ServerException catch (e) {
      return left(ServerFailure(e.message));
    }
  }

  @override
  Future<Either<Failure, Device>> updateDevice(
    String sbcId,
    String deviceFriendlyName,
  ) async {
    try {
      final device = await _remoteDataSource.updateDevice(
        sbcId,
        deviceFriendlyName,
      );
      return right(device);
    } on ServerException catch (e) {
      return left(ServerFailure(e.message));
    }
  }

  @override
  Future<Either<Failure, Unit>> deleteDevice(String sbcId) async {
    try {
      await _remoteDataSource.deleteDevice(sbcId);
      return right(unit);
    } on ServerException catch (e) {
      return left(ServerFailure(e.message));
    }
  }

  @override
  Future<Either<Failure, List<DeviceUser>>> getDeviceUsers(String sbcId) async {
    try {
      final users = await _remoteDataSource.getDeviceUsers(sbcId);
      return right(users);
    } on ServerException catch (e) {
      return left(ServerFailure(e.message));
    }
  }

  @override
  Future<Either<Failure, Unit>> addDeviceUser(
    String sbcId,
    String userEmail,
  ) async {
    try {
      await _remoteDataSource.addDeviceUser(sbcId, userEmail);
      return right(unit);
    } on ServerException catch (e) {
      return left(ServerFailure(e.message));
    }
  }

  @override
  Future<Either<Failure, Unit>> removeDeviceUser(
    String sbcId,
    String userId,
  ) async {
    try {
      await _remoteDataSource.removeDeviceUser(sbcId, userId);
      return right(unit);
    } on ServerException catch (e) {
      return left(ServerFailure(e.message));
    }
  }
}
