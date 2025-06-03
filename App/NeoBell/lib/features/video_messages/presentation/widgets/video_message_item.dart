import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../../domain/entities/video_message.dart';

class VideoMessageItem extends StatelessWidget {
  final VideoMessage message;
  final VoidCallback onPlay;
  final VoidCallback onDelete;

  const VideoMessageItem({
    super.key,
    required this.message,
    required this.onPlay,
    required this.onDelete,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: ListTile(
        leading: Stack(
          alignment: Alignment.center,
          children: [
            const Icon(Icons.videocam),
            if (!message.isViewed)
              Positioned(
                right: 0,
                top: 0,
                child: Container(
                  width: 8,
                  height: 8,
                  decoration: const BoxDecoration(
                    color: Colors.blue,
                    shape: BoxShape.circle,
                  ),
                ),
              ),
          ],
        ),
        title: Text(message.deviceFriendlyName),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              DateFormat('MMM d, y HH:mm').format(message.recordedAt),
              style: Theme.of(context).textTheme.bodySmall,
            ),
            if (message.visitorNameIfKnown != null)
              Text(
                'Visitor: ${message.visitorNameIfKnown}',
                style: Theme.of(context).textTheme.bodySmall,
              ),
            Text(
              'Duration: ${_formatDuration(message.durationSec)}',
              style: Theme.of(context).textTheme.bodySmall,
            ),
          ],
        ),
        trailing: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            IconButton(
              icon: const Icon(Icons.play_circle_outline),
              onPressed: onPlay,
            ),
            IconButton(
              icon: const Icon(Icons.delete_outline),
              onPressed: onDelete,
            ),
          ],
        ),
      ),
    );
  }

  String _formatDuration(int seconds) {
    final minutes = seconds ~/ 60;
    final remainingSeconds = seconds % 60;
    return '${minutes}m ${remainingSeconds}s';
  }
}
