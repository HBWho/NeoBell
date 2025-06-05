import 'dart:async';
import 'dart:convert';

import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:logger/web.dart';

import '../../../../core/theme/theme.dart';
import '../../domain/entities/notification_channel.dart';
import '../../domain/entities/notification_message.dart';

abstract class LocalNotificationsDataSource {
  Future<void> initialize();
  Future<void> showNotification(
    NotificationMessage message, {
    AndroidNotificationDetails? androidNotificationDetails,
  });
  Stream<Map<String, dynamic>> get onNotificationTap;
}

class LocalNotificationsDataSourceImpl implements LocalNotificationsDataSource {
  final FlutterLocalNotificationsPlugin _notifications;
  final Logger _logger = Logger();
  final StreamController<Map<String, dynamic>> _notificationTapController =
      StreamController<Map<String, dynamic>>.broadcast();
  @override
  Stream<Map<String, dynamic>> get onNotificationTap =>
      _notificationTapController.stream;

  LocalNotificationsDataSourceImpl(this._notifications);

  @override
  Future<void> initialize() async {
    try {
      const initializationSettings = InitializationSettings(
        android: AndroidInitializationSettings('notification_small_icon'),
      );

      await _notifications.initialize(
        initializationSettings,
        onDidReceiveNotificationResponse: (NotificationResponse response) {
          if (response.payload != null && response.payload!.isNotEmpty) {
            try {
              _notificationTapController.add(jsonDecode(response.payload!));
              _logger.d(
                'LocalNotificationsDataSourceImpl: Notification payload: ${jsonDecode(response.payload!)}',
              );
            } catch (e) {
              _logger.e(
                'LocalNotificationsDataSourceImpl: Error decoding notification payload: $e',
              );
            }
          }
        },
      );
      await _createNotificationChannels();
      _logger.i('Local notifications initialized');
    } catch (e) {
      _logger.e('Error initializing notifications: $e');
      rethrow;
    }
  }

  Future<void> _createNotificationChannels() async {
    for (var channel in NotificationChannel.values) {
      await _notifications
          .resolvePlatformSpecificImplementation<
            AndroidFlutterLocalNotificationsPlugin
          >()
          ?.createNotificationChannel(
            AndroidNotificationChannel(
              channel.id,
              channel.name,
              description: channel.description,
              importance: Importance.high,
            ),
          );
    }
  }

  @override
  Future<void> showNotification(
    NotificationMessage message, {
    AndroidNotificationDetails? androidNotificationDetails,
  }) async {
    try {
      final platformChannelSpecifics = NotificationDetails(
        android:
            androidNotificationDetails ??
            AndroidNotificationDetails(
              message.channel.id,
              message.channel.name,
              channelDescription: message.channel.description,
              importance: Importance.defaultImportance,
              priority: Priority.defaultPriority,
              icon: 'notification_small_icon',
              // largeIcon: DrawableResourceAndroidBitmap('notification_large_icon'),
              color: AppColors.primary,
            ),
      );

      await _notifications.show(
        DateTime.now().millisecondsSinceEpoch.hashCode,
        message.title,
        message.body,
        platformChannelSpecifics,
        payload: message.payload != null ? jsonEncode(message.payload) : null,
      );

      _logger.d('Notification shown: ${message.title}');
    } catch (e) {
      _logger.e('Error showing notification: $e');
      rethrow;
    }
  }
}
