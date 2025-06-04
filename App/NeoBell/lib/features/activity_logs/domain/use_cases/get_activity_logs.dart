import 'package:fpdart/fpdart.dart';
import '../../../../core/error/failure.dart';
import '../../../../core/usecase/usecase.dart';
import '../entities/activity_log_filter.dart';
import '../entities/activity_log_response.dart';
import '../repositories/activity_log_repository.dart';

class GetActivityLogs
    implements UseCase<ActivityLogResponse, ActivityLogFilter> {
  final ActivityLogRepository repository;

  const GetActivityLogs(this.repository);

  @override
  Future<Either<Failure, ActivityLogResponse>> call(
    ActivityLogFilter params,
  ) async {
    return await repository.getActivityLogs(params);
  }
}
