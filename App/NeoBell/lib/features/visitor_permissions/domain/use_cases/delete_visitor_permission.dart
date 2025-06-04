import 'package:fpdart/fpdart.dart';
import '../../../../core/error/failure.dart';
import '../../../../core/usecase/usecase.dart';
import '../repositories/visitor_permission_repository.dart';

class DeleteVisitorPermission
    implements UseCase<Unit, DeleteVisitorPermissionParams> {
  final VisitorPermissionRepository repository;

  DeleteVisitorPermission(this.repository);

  @override
  Future<Either<Failure, Unit>> call(
    DeleteVisitorPermissionParams params,
  ) async {
    // Validate input
    if (params.faceTagId.isEmpty) {
      return Left(Failure('Face tag ID cannot be empty'));
    }

    return await repository.deleteVisitorPermission(params.faceTagId);
  }
}

class DeleteVisitorPermissionParams {
  final String faceTagId;

  const DeleteVisitorPermissionParams({required this.faceTagId});
}
