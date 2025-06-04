import 'package:fpdart/fpdart.dart';

import '../../../../core/error/failure.dart';
import '../../../../core/error/server_exception.dart';
import '../../../../core/error/server_failure.dart';
import '../../domain/entities/create_package_delivery.dart';
import '../../domain/entities/package_delivery.dart';
import '../../domain/entities/package_delivery_filter.dart';
import '../../domain/entities/update_package_delivery.dart';
import '../../domain/repositories/package_delivery_repository.dart';
import '../datasources/package_delivery_remote_data_source.dart';

class PackageDeliveryRepositoryImpl implements PackageDeliveryRepository {
  final PackageDeliveryRemoteDataSource remoteDataSource;

  PackageDeliveryRepositoryImpl({required this.remoteDataSource});

  @override
  Future<Either<Failure, List<PackageDelivery>>> getPackageDeliveries({
    PackageDeliveryFilter? filter,
    int? limit,
    String? lastEvaluatedKey,
  }) async {
    try {
      final deliveries = await remoteDataSource.getPackageDeliveries(
        filter: filter,
        limit: limit,
        lastEvaluatedKey: lastEvaluatedKey,
      );
      return Right(deliveries);
    } on ServerException catch (e) {
      return Left(ServerFailure(e.message));
    } catch (e) {
      return Left(ServerFailure('Failed to get package deliveries: $e'));
    }
  }

  @override
  Future<Either<Failure, PackageDelivery>> getPackageDeliveryById(
    String orderId,
  ) async {
    try {
      final delivery = await remoteDataSource.getPackageDeliveryById(orderId);
      return Right(delivery);
    } on ServerException catch (e) {
      return Left(ServerFailure(e.message));
    } catch (e) {
      return Left(ServerFailure('Failed to get package delivery: $e'));
    }
  }

  @override
  Future<Either<Failure, PackageDelivery>> createPackageDelivery(
    CreatePackageDelivery delivery,
  ) async {
    try {
      final createdDelivery = await remoteDataSource.createPackageDelivery(
        delivery,
      );
      return Right(createdDelivery);
    } on ServerException catch (e) {
      return Left(ServerFailure(e.message));
    } catch (e) {
      return Left(ServerFailure('Failed to create package delivery: $e'));
    }
  }

  @override
  Future<Either<Failure, PackageDelivery>> updatePackageDelivery(
    String orderId,
    UpdatePackageDelivery delivery,
  ) async {
    try {
      final updatedDelivery = await remoteDataSource.updatePackageDelivery(
        orderId,
        delivery,
      );
      return Right(updatedDelivery);
    } on ServerException catch (e) {
      return Left(ServerFailure(e.message));
    } catch (e) {
      return Left(ServerFailure('Failed to update package delivery: $e'));
    }
  }

  @override
  Future<Either<Failure, void>> deletePackageDelivery(String orderId) async {
    try {
      await remoteDataSource.deletePackageDelivery(orderId);
      return const Right(null);
    } on ServerException catch (e) {
      return Left(ServerFailure(e.message));
    } catch (e) {
      return Left(ServerFailure('Failed to delete package delivery: $e'));
    }
  }
}
