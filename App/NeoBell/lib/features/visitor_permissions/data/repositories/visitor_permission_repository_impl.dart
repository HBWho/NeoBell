import 'package:fpdart/fpdart.dart';
import '../../../../core/error/failure.dart';
import '../../../../core/error/server_exception.dart';
import '../../domain/entities/visitor_permission.dart';
import '../../domain/entities/visitor_permission_with_image.dart';
import '../../domain/repositories/visitor_permission_repository.dart';
import '../datasources/visitor_permission_remote_data_source.dart';

class VisitorPermissionRepositoryImpl implements VisitorPermissionRepository {
  final VisitorPermissionRemoteDataSource remoteDataSource;

  VisitorPermissionRepositoryImpl({required this.remoteDataSource});

  @override
  Future<Either<Failure, List<VisitorPermission>>> getVisitorPermissions({
    int? limit,
    String? lastEvaluatedKey,
  }) async {
    try {
      final visitorPermissions = await remoteDataSource.getVisitorPermissions(
        limit: limit,
        lastEvaluatedKey: lastEvaluatedKey,
      );
      return Right(visitorPermissions);
    } on ServerException catch (e) {
      return Left(Failure(e.message));
    } catch (e) {
      return Left(Failure('An unexpected error occurred: $e'));
    }
  }

  @override
  Future<Either<Failure, VisitorPermissionWithImage>>
  getVisitorDetailsWithImage(String faceTagId) async {
    try {
      final visitorDetails = await remoteDataSource.getVisitorDetailsWithImage(
        faceTagId,
      );
      return Right(visitorDetails);
    } on ServerException catch (e) {
      return Left(Failure(e.message));
    } catch (e) {
      return Left(Failure('An unexpected error occurred: $e'));
    }
  }

  @override
  Future<Either<Failure, Unit>> updateVisitorPermission({
    required String faceTagId,
    required String visitorName,
    required PermissionLevel permissionLevel,
  }) async {
    try {
      await remoteDataSource.updateVisitorPermission(
        faceTagId: faceTagId,
        visitorName: visitorName,
        permissionLevel: permissionLevel.value,
      );
      return const Right(unit);
    } on ServerException catch (e) {
      return Left(Failure(e.message));
    } catch (e) {
      return Left(Failure('An unexpected error occurred: $e'));
    }
  }

  @override
  Future<Either<Failure, Unit>> deleteVisitorPermission(
    String faceTagId,
  ) async {
    try {
      await remoteDataSource.deleteVisitorPermission(faceTagId);
      return const Right(unit);
    } on ServerException catch (e) {
      return Left(Failure(e.message));
    } catch (e) {
      return Left(Failure('An unexpected error occurred: $e'));
    }
  }
}
