import 'package:fpdart/fpdart.dart';
import '../../../../core/error/failure.dart';
import '../../../../core/error/server_exception.dart';
import '../../domain/entities/activity_log_filter.dart';
import '../../domain/entities/activity_log_response.dart';
import '../../domain/repositories/activity_log_repository.dart';
import '../datasources/activity_log_remote_data_source.dart';

class ActivityLogRepositoryImpl implements ActivityLogRepository {
  final ActivityLogRemoteDataSource remoteDataSource;

  ActivityLogRepositoryImpl({required this.remoteDataSource});

  @override
  Future<Either<Failure, ActivityLogResponse>> getActivityLogs(
    ActivityLogFilter filter,
  ) async {
    try {
      final activityLogResponse = await remoteDataSource.getActivityLogs(
        filter,
      );
      return Right(activityLogResponse);
    } on ServerException catch (e) {
      return Left(Failure(e.message));
    } catch (e) {
      return Left(Failure('An unexpected error occurred: $e'));
    }
  }
}
