import 'dart:async';

import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:logger/logger.dart';

import '../../core/handlers/notification_background_handler.dart';
import '../../domain/entities/notification_channel.dart';
import '../../domain/entities/notification_message.dart';
import 'notification_local_data_source.dart';

abstract class NotificationRemoteDataSource {
  Stream<Map<String, dynamic>> get onNotificationTap;
  Future<void> initialize();
  Future<void> showLocalNotification(NotificationMessage message);
  Future<String?> getFirebaseToken();
}

class NotificationRemoteDataSourceImpl implements NotificationRemoteDataSource {
  final LocalNotificationsDataSource _localNotifications;
  final FirebaseMessaging _firebaseMessaging;
  final Logger _logger = Logger();
  final _notificationTapController =
      StreamController<Map<String, dynamic>>.broadcast();
  @override
  Stream<Map<String, dynamic>> get onNotificationTap =>
      _notificationTapController.stream;

  NotificationRemoteDataSourceImpl({
    required LocalNotificationsDataSource localNotifications,
    required FirebaseMessaging firebaseMessaging,
  }) : _localNotifications = localNotifications,
       _firebaseMessaging = firebaseMessaging;

  @override
  Future<void> initialize() async {
    await _requestPermissions();
    await _localNotifications.initialize();
    await _setupFirebaseMessaging();
    _logger.i('Firebase Notifications initialized');
  }

  Future<void> _requestPermissions() async {
    await _firebaseMessaging.requestPermission(
      alert: true,
      badge: true,
      sound: true,
    );
  }

  Future<void> _setupFirebaseMessaging() async {
    // Treatment of Messages received when the app is in background or terminated
    FirebaseMessaging.onBackgroundMessage(firebaseMessagingBackgroundHandler);
    // Messages received when the app is in foreground
    FirebaseMessaging.onMessage.listen(_handleForegroundMessage);
    // App opened from a notification when it was in BACKGROUND
    FirebaseMessaging.onMessageOpenedApp.listen((RemoteMessage message) {
      _logger.i(
        'NotificationRemoteDataSourceImpl: Message opened app from background via onMessageOpenedApp. Data: ${message.data}',
      );
      _notificationTapController.add(message.data);
    });
    // App opened from a notification when it was TERMINATED
    RemoteMessage? initialMessage =
        await _firebaseMessaging.getInitialMessage();
    if (initialMessage != null && initialMessage.data.isNotEmpty) {
      _logger.i(
        'NotificationRemoteDataSourceImpl: Message opened app from terminated state via getInitialMessage. Data: ${initialMessage.data}',
      );
      _notificationTapController.add(initialMessage.data);
    }
    _localNotifications.onNotificationTap.listen((data) {
      _notificationTapController.add(data);
    });
  }

  @override
  Future<void> showLocalNotification(NotificationMessage message) =>
      _localNotifications.showNotification(message);

  @override
  Future<String?> getFirebaseToken() => _firebaseMessaging.getToken();

  void _handleForegroundMessage(RemoteMessage message) {
    _logger.i(
      'Handling foreground message: \nTitle: ${message.notification?.title}\nBody: ${message.notification?.body}\nChannel: ${message.notification?.android?.channelId}\nData: ${message.data}',
    );

    final NotificationChannel channel =
        _getChannel(message.notification?.android?.channelId) ??
        _getChannel(message.data['notification_type'] as String?) ??
        NotificationChannel.system;

    showLocalNotification(
      NotificationMessage(
        title: message.notification?.title ?? 'New Message',
        body: message.notification?.body ?? '',
        channel: channel,
        payload: message.data,
      ),
    );
  }

  NotificationChannel? _getChannel(String? name) {
    if (name == null) {
      return null;
    }
    switch (name) {
      case 'package_delivery':
        return NotificationChannel.packageDelivery;
      case 'video_message':
        return NotificationChannel.videoMessages;
      case 'device_management':
        return NotificationChannel.deviceManagement;
      case 'user_actions':
        return NotificationChannel.userActions;
      case 'visitor_registration':
        return NotificationChannel.visitorRegistration;
      case 'system':
        return NotificationChannel.system;
      default:
        return null;
    }
  }
}
