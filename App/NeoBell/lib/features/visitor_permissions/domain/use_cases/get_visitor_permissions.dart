import 'package:fpdart/fpdart.dart';
import '../../../../core/error/failure.dart';
import '../../../../core/usecase/usecase.dart';
import '../entities/visitor_permission.dart';
import '../repositories/visitor_permission_repository.dart';

class GetVisitorPermissions
    implements UseCase<List<VisitorPermission>, GetVisitorPermissionsParams> {
  final VisitorPermissionRepository repository;

  GetVisitorPermissions(this.repository);

  @override
  Future<Either<Failure, List<VisitorPermission>>> call(
    GetVisitorPermissionsParams params,
  ) async {
    return await repository.getVisitorPermissions(
      limit: params.limit,
      lastEvaluatedKey: params.lastEvaluatedKey,
    );
  }
}

class GetVisitorPermissionsParams {
  final int? limit;
  final String? lastEvaluatedKey;

  const GetVisitorPermissionsParams({this.limit, this.lastEvaluatedKey});
}
