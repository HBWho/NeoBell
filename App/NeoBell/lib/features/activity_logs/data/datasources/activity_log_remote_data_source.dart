import '../../../../core/constants/api_constants.dart';
import '../../../../core/data/api_service.dart';
import '../../../../core/error/server_exception.dart';
import '../../domain/entities/activity_log_filter.dart';
import '../models/activity_log_response_model.dart';

abstract class ActivityLogRemoteDataSource {
  /// Gets activity logs from the API with filtering and pagination
  /// Throws a [ServerException] for all error codes
  Future<ActivityLogResponseModel> getActivityLogs(ActivityLogFilter filter);
}

class ActivityLogRemoteDataSourceImpl implements ActivityLogRemoteDataSource {
  final ApiService apiService;

  ActivityLogRemoteDataSourceImpl(this.apiService);

  @override
  Future<ActivityLogResponseModel> getActivityLogs(
    ActivityLogFilter filter,
  ) async {
    final queryParams = filter.toQueryParameters();

    final response = await apiService.getData(
      endPoint: ApiEndpoints.getActivityLogs,
      queryParams: queryParams.map(
        (key, value) => MapEntry(key, value.toString()),
      ),
    );

    return ActivityLogResponseModel.fromJson(response);
  }
}
