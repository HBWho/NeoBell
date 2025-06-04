import 'package:fpdart/fpdart.dart';
import '../../../../core/error/failure.dart';
import '../../../../core/usecase/usecase.dart';
import '../entities/visitor_permission_with_image.dart';
import '../repositories/visitor_permission_repository.dart';

class GetVisitorDetailsWithImage
    implements UseCase<VisitorPermissionWithImage, String> {
  final VisitorPermissionRepository repository;

  GetVisitorDetailsWithImage(this.repository);

  @override
  Future<Either<Failure, VisitorPermissionWithImage>> call(
    String faceTagId,
  ) async {
    // Validate input
    if (faceTagId.isEmpty) {
      return Left(Failure('Face tag ID cannot be empty'));
    }

    return await repository.getVisitorDetailsWithImage(faceTagId);
  }
}
