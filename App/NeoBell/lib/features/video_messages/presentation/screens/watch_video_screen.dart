import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import 'package:video_player/video_player.dart';
import '../../../../core/common/widgets/base_screen_widget.dart';
import '../../../../core/utils/show_snackbar.dart';
import '../../domain/entities/video_message.dart';
import '../blocs/video_message_bloc.dart';
import '../blocs/video_message_state.dart';

class WatchVideoScreen extends StatefulWidget {
  final String messageId;
  const WatchVideoScreen({super.key, required this.messageId});

  @override
  State<WatchVideoScreen> createState() => _WatchVideoScreenState();
}

class _WatchVideoScreenState extends State<WatchVideoScreen> {
  VideoPlayerController? _controller;
  bool _isInitialized = false;
  bool _isLoading = true;
  String? _errorMessage;
  VideoMessage? _videoMessage;

  @override
  void initState() {
    super.initState();
    _initializeVideo();
  }

  void _initializeVideo() {
    final videoState = context.read<VideoMessageBloc>().state;

    if (videoState is ViewUrlGenerated &&
        videoState.messageId == widget.messageId) {
      try {
        _videoMessage = videoState.messages.firstWhere(
          (msg) => msg.messageId == widget.messageId,
        );
      } catch (e) {
        _videoMessage = null;
      }

      _setupVideoPlayer(videoState.url);
    } else {
      setState(() {
        _errorMessage = 'Video URL not found';
        _isLoading = false;
      });
      Future.delayed(const Duration(seconds: 2), () {
        if (mounted) {
          context.pop();
        }
      });
    }
  }

  void _setupVideoPlayer(String url) {
    try {
      _controller = VideoPlayerController.networkUrl(Uri.parse(url));
      _controller!
          .initialize()
          .then((_) {
            if (mounted) {
              setState(() {
                _isInitialized = true;
                _isLoading = false;
              });
              _controller!.play();
            }
          })
          .catchError((error) {
            if (mounted) {
              setState(() {
                _errorMessage =
                    'Something went wrong while loading the video: $error';
                _isLoading = false;
              });
            }
          });
    } catch (e) {
      setState(() {
        _errorMessage = 'Error configuring player: $e';
        _isLoading = false;
      });
    }
  }

  @override
  void dispose() {
    _controller?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return BaseScreenWidget(
      title: _videoMessage?.visitorName ?? 'Watch Video',
      actions: [
        if (_videoMessage != null)
          IconButton(
            icon: const Icon(Icons.info_outline),
            onPressed: () => _showVideoInfo(context),
          ),
      ],
      body: BlocListener<VideoMessageBloc, VideoMessageState>(
        listener: (context, state) {
          if (state is VideoMessageError) {
            showSnackBar(context, message: state.message, isError: true);
            Future.delayed(const Duration(seconds: 2), () {
              if (context.mounted) context.pop();
            });
          } else if (state is VideoMessageInitial) {
            showSnackBar(
              context,
              message: 'Dados foram atualizados',
              isSucess: true,
            );
            Future.delayed(const Duration(seconds: 1), () {
              if (context.mounted) context.pop();
            });
          }
        },
        child: _buildBody(),
      ),
    );
  }

  Widget _buildBody() {
    if (_isLoading) {
      return const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            CircularProgressIndicator(),
            SizedBox(height: 16),
            Text('Loading video...'),
          ],
        ),
      );
    }

    if (_errorMessage != null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(Icons.error_outline, size: 64, color: Colors.red),
            const SizedBox(height: 16),
            Text(
              _errorMessage!,
              textAlign: TextAlign.center,
              style: const TextStyle(fontSize: 16),
            ),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: () => context.pop(),
              child: const Text('Voltar'),
            ),
          ],
        ),
      );
    }

    if (!_isInitialized || _controller == null) {
      return const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            CircularProgressIndicator(),
            SizedBox(height: 16),
            Text('Initializing player...'),
          ],
        ),
      );
    }

    return Column(
      children: [
        // Informações do vídeo
        if (_videoMessage != null) _buildVideoInfo(),

        // Player de vídeo
        Expanded(
          child: Padding(
            padding: const EdgeInsets.all(16.0),
            child: Center(
              child: LayoutBuilder(
                builder: (context, constraints) {
                  final screenSize = MediaQuery.of(context).size;
                  final maxWidth = screenSize.width - 32; // Account for padding
                  final maxHeight = constraints.maxHeight - 32;
                  final videoAspectRatio = _controller!.value.aspectRatio;
                  // Calculate dimensions that fit within constraints
                  double width = maxWidth;
                  double height = width / videoAspectRatio;

                  if (height > maxHeight) {
                    height = maxHeight;
                    width = height * videoAspectRatio;
                  }

                  return Container(
                    width: width,
                    height: height,
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(8),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.black.withAlpha(
                            Color.getAlphaFromOpacity(0.3),
                          ),
                          blurRadius: 10,
                          offset: const Offset(0, 5),
                        ),
                      ],
                    ),
                    child: ClipRRect(
                      borderRadius: BorderRadius.circular(8),
                      child: Stack(
                        children: [
                          VideoPlayer(_controller!),
                          _buildVideoControls(),
                        ],
                      ),
                    ),
                  );
                },
              ),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildVideoInfo() {
    final message = _videoMessage!;
    return Container(
      padding: const EdgeInsets.all(16),
      margin: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        color: Colors.grey[100],
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.person, size: 20),
              const SizedBox(width: 8),
              Text(
                message.visitorName,
                style: const TextStyle(
                  fontWeight: FontWeight.bold,
                  fontSize: 16,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              const Icon(Icons.access_time, size: 16),
              const SizedBox(width: 8),
              Text(
                '${message.recordedAt.day}/${message.recordedAt.month}/${message.recordedAt.year} às ${message.recordedAt.hour.toString().padLeft(2, '0')}:${message.recordedAt.minute.toString().padLeft(2, '0')}',
              ),
            ],
          ),
          const SizedBox(height: 4),
          Row(
            children: [
              const Icon(Icons.timer, size: 16),
              const SizedBox(width: 8),
              Text('Duration: ${message.durationSec}s'),
              const Spacer(),
              Text(
                'Device: ${message.deviceFriendlyName}',
                style: const TextStyle(fontSize: 12),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildVideoControls() {
    return Positioned.fill(
      child: GestureDetector(
        onTap: () {
          setState(() {
            if (_controller!.value.isPlaying) {
              _controller!.pause();
            } else {
              _controller!.play();
            }
          });
        },
        child: Container(
          color: Colors.transparent,
          child: Center(
            child: AnimatedOpacity(
              opacity: _controller!.value.isPlaying ? 0.0 : 0.8,
              duration: const Duration(milliseconds: 300),
              child: Container(
                decoration: const BoxDecoration(
                  color: Colors.black54,
                  shape: BoxShape.circle,
                ),
                padding: const EdgeInsets.all(16),
                child: Icon(
                  _controller!.value.isPlaying ? Icons.pause : Icons.play_arrow,
                  color: Colors.white,
                  size: 48,
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  void _showVideoInfo(BuildContext context) {
    final message = _videoMessage!;
    showDialog(
      context: context,
      builder:
          (context) => AlertDialog(
            title: const Text('Informações do Vídeo'),
            content: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _buildInfoRow('Visitor:', message.visitorName),
                _buildInfoRow('Message ID:', message.messageId),
                _buildInfoRow('Device:', message.deviceFriendlyName),
                _buildInfoRow(
                  'Date:',
                  '${message.recordedAt.day}/${message.recordedAt.month}/${message.recordedAt.year}',
                ),
                _buildInfoRow(
                  'Time:',
                  '${message.recordedAt.hour.toString().padLeft(2, '0')}:${message.recordedAt.minute.toString().padLeft(2, '0')}',
                ),
                _buildInfoRow('Duration:', '${message.durationSec} seconds'),
                _buildInfoRow('Viewed:', message.isViewed ? 'Yes' : 'NNo'),
              ],
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(context),
                child: const Text('Fechar'),
              ),
            ],
          ),
    );
  }

  Widget _buildInfoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 80,
            child: Text(
              label,
              style: const TextStyle(fontWeight: FontWeight.bold),
            ),
          ),
          Expanded(child: Text(value)),
        ],
      ),
    );
  }
}
