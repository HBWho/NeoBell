import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../../../core/utils/show_snackbar.dart';
import '../../domain/entities/video_message.dart';
import '../blocs/video_message_bloc.dart';
import '../blocs/video_message_event.dart';
import '../blocs/video_message_state.dart';
import '../widgets/video_message_item.dart';
import '../widgets/video_message_filters.dart';

class VideoMessagesScreen extends StatelessWidget {
  const VideoMessagesScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Video Messages'),
        actions: [
          IconButton(
            icon: const Icon(Icons.filter_list),
            onPressed: () => _showFilters(context),
          ),
        ],
      ),
      body: BlocConsumer<VideoMessageBloc, VideoMessageState>(
        listener: (context, state) {
          if (state is VideoMessageError) {
            showSnackBar(
              context,
              message: state.message,
              isError: true,
            );
          }
        },
        builder: (context, state) {
          if (state is VideoMessageLoading) {
            return const Center(child: CircularProgressIndicator());
          }

          if (state is VideoMessagesLoadSuccess) {
            return _buildMessageList(context, state.messages);
          }

          return const Center(
            child: Text('No messages available'),
          );
        },
      ),
    );
  }

  Widget _buildMessageList(BuildContext context, List<VideoMessage> messages) {
    if (messages.isEmpty) {
      return const Center(
        child: Text('No messages found'),
      );
    }

    return RefreshIndicator(
      onRefresh: () async {
        context.read<VideoMessageBloc>().add(
              const GetVideoMessagesEvent(),
            );
      },
      child: ListView.builder(
        itemCount: messages.length,
        itemBuilder: (context, index) {
          final message = messages[index];
          return VideoMessageItem(
            message: message,
            onPlay: () => _playVideo(context, message),
            onDelete: () => _deleteMessage(context, message),
          );
        },
      ),
    );
  }

  void _showFilters(BuildContext context) {
    showModalBottomSheet(
      context: context,
      builder: (context) => const VideoMessageFilters(),
    );
  }

  void _playVideo(BuildContext context, VideoMessage message) {
    context.read<VideoMessageBloc>().add(
          GenerateViewUrlEvent(message.messageId),
        );

    // Mark as viewed when playing
    if (!message.isViewed) {
      context.read<VideoMessageBloc>().add(
            MarkAsViewedEvent(message.messageId),
          );
    }
  }

  void _deleteMessage(BuildContext context, VideoMessage message) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Delete Message'),
        content: const Text('Are you sure you want to delete this message?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () {
              context.read<VideoMessageBloc>().add(
                    DeleteMessageEvent(message.messageId),
                  );
              Navigator.pop(context);
            },
            child: const Text(
              'Delete',
              style: TextStyle(color: Colors.red),
            ),
          ),
        ],
      ),
    );
  }
}
