import 'package:flutter_bloc/flutter_bloc.dart';
import '../../domain/use_cases/delete_message.dart';
import '../../domain/use_cases/generate_view_url.dart';
import '../../domain/use_cases/get_video_messages.dart';
import '../../domain/use_cases/mark_as_viewed.dart';
import 'video_message_event.dart';
import 'video_message_state.dart';

class VideoMessageBloc extends Bloc<VideoMessageEvent, VideoMessageState> {
  final GetVideoMessages _getVideoMessages;
  final GenerateViewUrl _generateViewUrl;
  final MarkAsViewed _markAsViewed;
  final DeleteMessage _deleteMessage;

  VideoMessageBloc({
    required GetVideoMessages getVideoMessages,
    required GenerateViewUrl generateViewUrl,
    required MarkAsViewed markAsViewed,
    required DeleteMessage deleteMessage,
  })  : _getVideoMessages = getVideoMessages,
        _generateViewUrl = generateViewUrl,
        _markAsViewed = markAsViewed,
        _deleteMessage = deleteMessage,
        super(VideoMessageInitial()) {
    on<GetVideoMessagesEvent>(_onGetVideoMessages);
    on<GenerateViewUrlEvent>(_onGenerateViewUrl);
    on<MarkAsViewedEvent>(_onMarkAsViewed);
    on<DeleteMessageEvent>(_onDeleteMessage);
  }

  Future<void> _onGetVideoMessages(
    GetVideoMessagesEvent event,
    Emitter<VideoMessageState> emit,
  ) async {
    emit(VideoMessageLoading());

    final result = await _getVideoMessages(
      GetVideoMessagesParams(
        sbcId: event.sbcId,
        startDate: event.startDate,
        endDate: event.endDate,
        isViewed: event.isViewed,
        limit: event.limit,
        lastEvaluatedKey: event.lastEvaluatedKey,
      ),
    );

    result.fold(
      (failure) => emit(VideoMessageError(failure.message)),
      (messages) => emit(VideoMessagesLoadSuccess(messages: messages)),
    );
  }

  Future<void> _onGenerateViewUrl(
    GenerateViewUrlEvent event,
    Emitter<VideoMessageState> emit,
  ) async {
    emit(VideoMessageLoading());

    final result = await _generateViewUrl(event.messageId);

    result.fold(
      (failure) => emit(VideoMessageError(failure.message)),
      (url) => emit(ViewUrlGenerated(url: url, messageId: event.messageId)),
    );
  }

  Future<void> _onMarkAsViewed(
    MarkAsViewedEvent event,
    Emitter<VideoMessageState> emit,
  ) async {
    emit(VideoMessageLoading());

    final result = await _markAsViewed(event.messageId);

    result.fold(
      (failure) => emit(VideoMessageError(failure.message)),
      (_) => emit(MessageMarkedAsViewed(event.messageId)),
    );
  }

  Future<void> _onDeleteMessage(
    DeleteMessageEvent event,
    Emitter<VideoMessageState> emit,
  ) async {
    emit(VideoMessageLoading());

    final result = await _deleteMessage(event.messageId);

    result.fold(
      (failure) => emit(VideoMessageError(failure.message)),
      (_) => emit(MessageDeleted(event.messageId)),
    );
  }
}
