import 'package:fpdart/fpdart.dart';
import '../../../../core/error/failure.dart';
import '../../../../core/usecase/usecase.dart';
import '../entities/visitor_permission.dart';
import '../repositories/visitor_permission_repository.dart';

class UpdateVisitorPermission
    implements UseCase<Unit, UpdateVisitorPermissionParams> {
  final VisitorPermissionRepository repository;

  UpdateVisitorPermission(this.repository);

  @override
  Future<Either<Failure, Unit>> call(
    UpdateVisitorPermissionParams params,
  ) async {
    // Validate input
    if (params.faceTagId.isEmpty) {
      return Left(Failure('Face tag ID cannot be empty'));
    }

    if (params.visitorName.trim().isEmpty) {
      return Left(Failure('Visitor name cannot be empty'));
    }

    return await repository.updateVisitorPermission(
      faceTagId: params.faceTagId,
      visitorName: params.visitorName.trim(),
      permissionLevel: params.permissionLevel,
    );
  }
}

class UpdateVisitorPermissionParams {
  final String faceTagId;
  final String visitorName;
  final PermissionLevel permissionLevel;

  const UpdateVisitorPermissionParams({
    required this.faceTagId,
    required this.visitorName,
    required this.permissionLevel,
  });
}
