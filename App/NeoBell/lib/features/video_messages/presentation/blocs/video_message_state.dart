import 'package:equatable/equatable.dart';
import '../../domain/entities/video_message.dart';

abstract class VideoMessageState extends Equatable {
  final List<VideoMessage> messages;
  const VideoMessageState({this.messages = const []});

  @override
  List<Object?> get props => [messages];
}

class VideoMessageInitial extends VideoMessageState {}

class VideoMessageLoading extends VideoMessageState {
  const VideoMessageLoading({super.messages});

  @override
  List<Object?> get props => [messages];
}

class VideoMessagesLoadSuccess extends VideoMessageState {
  final String? lastEvaluatedKey;

  const VideoMessagesLoadSuccess({
    required super.messages,
    this.lastEvaluatedKey,
  });

  @override
  List<Object?> get props => [messages, lastEvaluatedKey];
}

class VideoMessageError extends VideoMessageState {
  final String message;

  const VideoMessageError(this.message, {super.messages});

  @override
  List<Object> get props => [message];
}

class ViewUrlGenerated extends VideoMessageState {
  final String url;
  final String messageId;

  const ViewUrlGenerated({
    required this.url,
    required this.messageId,
    super.messages,
  });

  @override
  List<Object> get props => [url, messageId, messages];
}

class MessageDeleted extends VideoMessageState {
  final String messageId;

  const MessageDeleted(this.messageId, {super.messages});

  @override
  List<Object> get props => [messageId, messages];
}
