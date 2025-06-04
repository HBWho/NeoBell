import 'package:fpdart/fpdart.dart';
import '../../../../core/error/failure.dart';
import '../entities/visitor_permission.dart';
import '../entities/visitor_permission_with_image.dart';

abstract class VisitorPermissionRepository {
  Future<Either<Failure, List<VisitorPermission>>> getVisitorPermissions({
    int? limit,
    String? lastEvaluatedKey,
  });

  Future<Either<Failure, VisitorPermissionWithImage>>
  getVisitorDetailsWithImage(String faceTagId);

  Future<Either<Failure, Unit>> updateVisitorPermission({
    required String faceTagId,
    required String visitorName,
    required PermissionLevel permissionLevel,
  });

  Future<Either<Failure, Unit>> deleteVisitorPermission(String faceTagId);
}
