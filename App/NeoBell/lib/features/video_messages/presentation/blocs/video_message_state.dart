import 'package:equatable/equatable.dart';
import '../../domain/entities/video_message.dart';

abstract class VideoMessageState extends Equatable {
  const VideoMessageState();

  @override
  List<Object?> get props => [];
}

class VideoMessageInitial extends VideoMessageState {}

class VideoMessageLoading extends VideoMessageState {}

class VideoMessagesLoadSuccess extends VideoMessageState {
  final List<VideoMessage> messages;
  final String? lastEvaluatedKey;

  const VideoMessagesLoadSuccess({
    required this.messages,
    this.lastEvaluatedKey,
  });

  @override
  List<Object?> get props => [messages, lastEvaluatedKey];
}

class VideoMessageError extends VideoMessageState {
  final String message;

  const VideoMessageError(this.message);

  @override
  List<Object> get props => [message];
}

class ViewUrlGenerated extends VideoMessageState {
  final String url;
  final String messageId;

  const ViewUrlGenerated({
    required this.url,
    required this.messageId,
  });

  @override
  List<Object> get props => [url, messageId];
}

class MessageMarkedAsViewed extends VideoMessageState {
  final String messageId;

  const MessageMarkedAsViewed(this.messageId);

  @override
  List<Object> get props => [messageId];
}

class MessageDeleted extends VideoMessageState {
  final String messageId;

  const MessageDeleted(this.messageId);

  @override
  List<Object> get props => [messageId];
}
