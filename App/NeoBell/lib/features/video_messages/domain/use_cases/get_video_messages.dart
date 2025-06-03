import 'package:fpdart/fpdart.dart';
import '../../../../core/error/failure.dart';
import '../../../../core/usecase/usecase.dart';
import '../entities/video_message.dart';
import '../repositories/video_message_repository.dart';

class GetVideoMessagesParams {
  final String? sbcId;
  final DateTime? startDate;
  final DateTime? endDate;
  final bool? isViewed;
  final int? limit;
  final String? lastEvaluatedKey;

  GetVideoMessagesParams({
    this.sbcId,
    this.startDate,
    this.endDate,
    this.isViewed,
    this.limit,
    this.lastEvaluatedKey,
  });
}

class GetVideoMessages
    implements UseCase<List<VideoMessage>, GetVideoMessagesParams> {
  final VideoMessageRepository repository;

  GetVideoMessages(this.repository);

  @override
  Future<Either<Failure, List<VideoMessage>>> call(
      GetVideoMessagesParams params) async {
    return await repository.getVideoMessages(
      sbcId: params.sbcId,
      startDate: params.startDate,
      endDate: params.endDate,
      isViewed: params.isViewed,
      limit: params.limit,
      lastEvaluatedKey: params.lastEvaluatedKey,
    );
  }
}
