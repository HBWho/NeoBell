import '../../../../core/constants/api_constants.dart';
import '../../../../core/data/api_service.dart';
import '../../../../core/error/server_exception.dart';
import '../models/video_message_model.dart';

abstract class VideoMessageRemoteDataSource {
  /// Gets video messages from the API
  /// Throws a [ServerException] for all error codes
  Future<List<VideoMessageModel>> getVideoMessages({
    String? sbcId,
    DateTime? startDate,
    DateTime? endDate,
    bool? isViewed,
    int? limit,
    String? lastEvaluatedKey,
  });

  /// Generates a secure URL for viewing the video message
  /// Throws a [ServerException] for all error codes
  Future<String> generateViewUrl(String messageId);

  /// Marks a video message as viewed
  /// Throws a [ServerException] for all error codes
  Future<void> markAsViewed(String messageId);

  /// Deletes a video message
  /// Throws a [ServerException] for all error codes
  Future<void> deleteMessage(String messageId);
}

class VideoMessageRemoteDataSourceImpl implements VideoMessageRemoteDataSource {
  final ApiService apiService;

  VideoMessageRemoteDataSourceImpl(this.apiService);

  @override
  Future<List<VideoMessageModel>> getVideoMessages({
    String? sbcId,
    DateTime? startDate,
    DateTime? endDate,
    bool? isViewed,
    int? limit,
    String? lastEvaluatedKey,
  }) async {
    try {
      Map<String, String> queryParams = {};

      if (sbcId != null) queryParams['sbc_id'] = sbcId;
      if (startDate != null) {
        queryParams['start_date'] = startDate.toIso8601String();
      }
      if (endDate != null) queryParams['end_date'] = endDate.toIso8601String();
      if (isViewed != null) queryParams['is_viewed'] = isViewed.toString();
      if (limit != null) queryParams['limit'] = limit.toString();
      if (lastEvaluatedKey != null) {
        queryParams['last_evaluated_key'] = lastEvaluatedKey;
      }

      final response = await apiService.getData(
        endPoint: ApiEndpoints.getVideoMessages,
        queryParams: queryParams,
      );

      final List<dynamic> jsonList = response['messages'];
      return jsonList.map((json) => VideoMessageModel.fromJson(json)).toList();
    } on ServerException {
      rethrow;
    } catch (e) {
      throw ServerException('Failed to fetch video messages: $e');
    }
  }

  @override
  Future<String> generateViewUrl(String messageId) async {
    try {
      final response = await apiService.postData(
        endPoint: ApiEndpoints.generateViewUrl,
        pathParams: {'message_id': messageId},
      );
      return response['view_url'];
    } on ServerException {
      rethrow;
    } catch (e) {
      throw ServerException('Failed to generate view URL: $e');
    }
  }

  @override
  Future<void> markAsViewed(String messageId) async {
    try {
      await apiService.updateData(
        endPoint: ApiEndpoints.markAsViewed,
        pathParams: {'message_id': messageId},
        body: {'is_viewed': true},
      );
    } on ServerException {
      rethrow;
    } catch (e) {
      throw ServerException('Failed to mark message as viewed: $e');
    }
  }

  @override
  Future<void> deleteMessage(String messageId) async {
    try {
      await apiService.deleteData(
        endPoint: ApiEndpoints.deleteMessage,
        pathParams: {'message_id': messageId},
      );
    } on ServerException {
      rethrow;
    } catch (e) {
      throw ServerException('Failed to delete message: $e');
    }
  }
}
