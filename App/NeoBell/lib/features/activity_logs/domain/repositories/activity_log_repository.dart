import 'package:fpdart/fpdart.dart';
import '../../../../core/error/failure.dart';
import '../entities/activity_log_filter.dart';
import '../entities/activity_log_response.dart';

abstract class ActivityLogRepository {
  Future<Either<Failure, ActivityLogResponse>> getActivityLogs(
    ActivityLogFilter filter,
  );
}
