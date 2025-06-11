import 'package:app_settings/app_settings.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:logger/logger.dart';
import '../../../../core/utils/show_snackbar.dart';
import '../../domain/entities/notification_channel.dart';
import '../cubit/notification_cubit.dart';

class NotificationSettingsDialog extends StatefulWidget {
  const NotificationSettingsDialog({super.key});
  @override
  State<NotificationSettingsDialog> createState() =>
      _NotificationSettingsDialogState();
}

class _NotificationSettingsDialogState
    extends State<NotificationSettingsDialog> {
  final Logger _logger = Logger();
  String firebaseToken = '';

  Future<void> _openChannelSettings(
    BuildContext context,
    String channelId,
  ) async {
    try {
      await const MethodChannel(
        'neobell/notifications',
      ).invokeMethod('openChannelSettings', {'channelId': channelId});
    } catch (e) {
      _logger.e("Error opening channel settings: $e");
    }
  }

  Future<void> _openNotificationSettings() async {
    AppSettings.openAppSettings(type: AppSettingsType.notification);
  }

  Widget _buildChannelTile(NotificationChannel channel, bool isEnabled) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final isSmallScreen = constraints.maxWidth < 400;
        return Card(
          margin: const EdgeInsets.symmetric(vertical: 4, horizontal: 8),
          child: Padding(
            padding: const EdgeInsets.all(8.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  channel.name,
                  style: Theme.of(context).textTheme.titleMedium,
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 4),
                Text(
                  channel.description,
                  style: Theme.of(context).textTheme.bodySmall,
                ),
                const SizedBox(height: 8),
                if (isSmallScreen)
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                    children: [
                      IconButton(
                        icon: const Icon(Icons.notifications),
                        tooltip: 'Send Test Notification',
                        onPressed:
                            () => context
                                .read<NotificationCubit>()
                                .showNotification(
                                  title: 'Test: ${channel.name}',
                                  body:
                                      'This is a test notification for: ${channel.description}',
                                  channel: channel,
                                ),
                      ),
                      IconButton(
                        icon: const Icon(Icons.settings),
                        tooltip: 'Advanced Channel Settings',
                        onPressed:
                            () => _openChannelSettings(context, channel.id),
                      ),
                    ],
                  )
                else
                  Row(
                    mainAxisAlignment: MainAxisAlignment.end,
                    children: [
                      IconButton(
                        icon: const Icon(Icons.notifications),
                        tooltip: 'Send Test Notification',
                        onPressed:
                            () => context
                                .read<NotificationCubit>()
                                .showNotification(
                                  title: 'Test ${channel.name}',
                                  body:
                                      'This is a test notification for: ${channel.description}',
                                  channel: channel,
                                ),
                      ),
                      IconButton(
                        icon: const Icon(Icons.settings),
                        tooltip: 'Advanced Channel Settings',
                        onPressed:
                            () => _openChannelSettings(context, channel.id),
                      ),
                    ],
                  ),
              ],
            ),
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return BlocConsumer<NotificationCubit, NotificationState>(
      listener: (context, state) {
        if (state is NotificationError) {
          showSnackBar(
            context,
            message: 'Error: ${state.message}',
            isError: true,
          );
        }
      },
      builder: (context, state) {
        Map<NotificationChannel, bool> channelEnabledStates = {};
        if (state is NotificationChannelStatesLoaded) {
          channelEnabledStates = state.channelStates;
        }
        return AlertDialog(
          title: const Text('Notification Settings'),
          content: Container(
            constraints: const BoxConstraints(maxHeight: 400),
            width: double.maxFinite,
            child: SingleChildScrollView(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  ...NotificationChannel.values.map(
                    (channel) => _buildChannelTile(
                      channel,
                      channelEnabledStates[channel] ?? true,
                    ),
                  ),
                  const Divider(),
                  TextButton(
                    onPressed: _openNotificationSettings,
                    child: const Text('Advanced System Settings'),
                  ),
                  TextButton(
                    onPressed:
                        () => context
                            .read<NotificationCubit>()
                            .getFirebaseToken()
                            .then((value) {
                              setState(
                                () =>
                                    firebaseToken =
                                        value ?? 'Error obtaining token',
                              );
                            }),
                    child: const Text('Get Firebase Token'),
                  ),
                  if (firebaseToken.isNotEmpty)
                    Padding(
                      padding: const EdgeInsets.all(8.0),
                      child: SelectableText.rich(
                        TextSpan(
                          children: [
                            const TextSpan(text: 'Firebase Token: '),
                            TextSpan(
                              text: firebaseToken,
                              style: const TextStyle(
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ],
                        ),
                        textAlign: TextAlign.center,
                        onTap:
                            () => Clipboard.setData(
                              ClipboardData(text: firebaseToken),
                            ),
                      ),
                    ),
                ],
              ),
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Close'),
            ),
          ],
        );
      },
    );
  }
}
