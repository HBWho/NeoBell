import 'package:fpdart/fpdart.dart';
import '../../../../core/error/failure.dart';
import '../../../../core/error/server_failure.dart';
import '../../../../core/error/server_exception.dart';
import '../../domain/entities/video_message.dart';
import '../../domain/repositories/video_message_repository.dart';
import '../datasources/video_message_remote_data_source.dart';

class VideoMessageRepositoryImpl implements VideoMessageRepository {
  final VideoMessageRemoteDataSource remoteDataSource;

  VideoMessageRepositoryImpl(this.remoteDataSource);

  @override
  Future<Either<Failure, List<VideoMessage>>> getVideoMessages({
    String? sbcId,
    DateTime? startDate,
    DateTime? endDate,
    bool? isViewed,
    int? limit,
    String? lastEvaluatedKey,
  }) async {
    try {
      final result = await remoteDataSource.getVideoMessages(
        sbcId: sbcId,
        startDate: startDate,
        endDate: endDate,
        isViewed: isViewed,
        limit: limit,
        lastEvaluatedKey: lastEvaluatedKey,
      );
      return right(result);
    } on ServerException catch (e) {
      return left(ServerFailure(e.toString()));
    }
  }

  @override
  Future<Either<Failure, String>> generateViewUrl(String messageId) async {
    try {
      final result = await remoteDataSource.generateViewUrl(messageId);
      return right(result);
    } on ServerException catch (e) {
      return left(ServerFailure(e.toString()));
    }
  }

  @override
  Future<Either<Failure, void>> markAsViewed(String messageId) async {
    try {
      await remoteDataSource.markAsViewed(messageId);
      return right(null);
    } on ServerException catch (e) {
      return left(ServerFailure(e.toString()));
    }
  }

  @override
  Future<Either<Failure, void>> deleteMessage(String messageId) async {
    try {
      await remoteDataSource.deleteMessage(messageId);
      return right(null);
    } on ServerException catch (e) {
      return left(ServerFailure(e.toString()));
    }
  }
}
