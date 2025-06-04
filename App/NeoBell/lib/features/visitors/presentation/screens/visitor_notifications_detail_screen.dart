import 'package:flutter/material.dart';
import 'package:video_player/video_player.dart';
import '../../../../core/common/widgets/base_screen_widget.dart';

class VisitorNotificationDetailScreen extends StatelessWidget {
  final Map<String, String> notification;

  const VisitorNotificationDetailScreen({super.key, required this.notification});

  @override
  Widget build(BuildContext context) {
    final name = notification['name'] ?? 'Visitor';
    final videoUrl = notification['videoUrl'] ?? '';

    return BaseScreenWidget(
      title: name,
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('MESSAGE VIDEO:', style: TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            AspectRatio(
              aspectRatio: 16 / 9,
              child: _VideoPlayerWidget(videoUrl: videoUrl),
            ),
          ],
        ),
      ),
      bottomNavigationBar: Padding(
        padding: const EdgeInsets.all(12.0),
        child: ElevatedButton(
          onPressed: () => Navigator.pop(context),
          child: const Text('Return'),
        ),
      ),
    );
  }
}

class _VideoPlayerWidget extends StatefulWidget {
  final String videoUrl;

  const _VideoPlayerWidget({required this.videoUrl});

  @override
  State<_VideoPlayerWidget> createState() => _VideoPlayerWidgetState();
}

class _VideoPlayerWidgetState extends State<_VideoPlayerWidget> {
  late VideoPlayerController _controller;

  @override
  void initState() {
    super.initState();
    _controller = VideoPlayerController.network(widget.videoUrl)
      ..initialize().then((_) {
        setState(() {});
        _controller.play();
      });
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return _controller.value.isInitialized
        ? VideoPlayer(_controller)
        : const Center(child: CircularProgressIndicator());
  }
}
