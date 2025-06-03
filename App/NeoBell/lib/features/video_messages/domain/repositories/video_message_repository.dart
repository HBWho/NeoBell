import 'package:fpdart/fpdart.dart';
import '../../../../core/error/failure.dart';
import '../entities/video_message.dart';

abstract class VideoMessageRepository {
  /// Get a list of video messages with optional filters
  Future<Either<Failure, List<VideoMessage>>> getVideoMessages({
    String? sbcId,
    DateTime? startDate,
    DateTime? endDate,
    bool? isViewed,
    int? limit,
    String? lastEvaluatedKey,
  });

  /// Generate a secure URL for viewing a video message
  Future<Either<Failure, String>> generateViewUrl(String messageId);

  /// Mark a video message as viewed
  Future<Either<Failure, void>> markAsViewed(String messageId);

  /// Delete a video message
  Future<Either<Failure, void>> deleteMessage(String messageId);
}
