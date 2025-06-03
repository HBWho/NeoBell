import 'package:equatable/equatable.dart';

abstract class VideoMessageEvent extends Equatable {
  const VideoMessageEvent();

  @override
  List<Object?> get props => [];
}

class GetVideoMessagesEvent extends VideoMessageEvent {
  final String? sbcId;
  final DateTime? startDate;
  final DateTime? endDate;
  final bool? isViewed;
  final int? limit;
  final String? lastEvaluatedKey;

  const GetVideoMessagesEvent({
    this.sbcId,
    this.startDate,
    this.endDate,
    this.isViewed,
    this.limit,
    this.lastEvaluatedKey,
  });

  @override
  List<Object?> get props =>
      [sbcId, startDate, endDate, isViewed, limit, lastEvaluatedKey];
}

class GenerateViewUrlEvent extends VideoMessageEvent {
  final String messageId;

  const GenerateViewUrlEvent(this.messageId);

  @override
  List<Object> get props => [messageId];
}

class MarkAsViewedEvent extends VideoMessageEvent {
  final String messageId;

  const MarkAsViewedEvent(this.messageId);

  @override
  List<Object> get props => [messageId];
}

class DeleteMessageEvent extends VideoMessageEvent {
  final String messageId;

  const DeleteMessageEvent(this.messageId);

  @override
  List<Object> get props => [messageId];
}
