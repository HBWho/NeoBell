import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:logger/logger.dart';

import '../../core/handlers/notification_background_handler.dart';
import '../../domain/entities/notification_channel.dart';
import '../../domain/entities/notification_message.dart';
import 'notification_local_data_source.dart';

abstract class NotificationRemoteDataSource {
  Future<void> initialize();
  Future<void> showLocalNotification(NotificationMessage message);
  Future<String?> getFirebaseToken();
  Future<void> handleBackgroundMessage();
}

class NotificationRemoteDataSourceImpl implements NotificationRemoteDataSource {
  final LocalNotificationsDataSource _localNotifications;
  final FirebaseMessaging _firebaseMessaging;
  final Logger _logger = Logger();

  NotificationRemoteDataSourceImpl({
    required LocalNotificationsDataSource localNotifications,
    required FirebaseMessaging firebaseMessaging,
  })  : _localNotifications = localNotifications,
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
    FirebaseMessaging.onMessage.listen(_handleForegroundMessage);
    FirebaseMessaging.onBackgroundMessage(firebaseMessagingBackgroundHandler);
  }

  @override
  Future<void> showLocalNotification(NotificationMessage message) =>
      _localNotifications.showNotification(message);

  @override
  Future<String?> getFirebaseToken() => _firebaseMessaging.getToken();

  void _handleForegroundMessage(RemoteMessage message) {
    _logger.i(
        'Handling foreground message: \nTitle: ${message.notification?.title}\nBody: ${message.notification?.body}\nChannel: ${message.notification?.android?.channelId}\nData: ${message.data}');

    final NotificationChannel channel =
        _getChannel(message.notification?.android?.channelId) ??
            _getChannel(message.data['category'] as String?) ??
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
      case 'inventory':
        return NotificationChannel.inventory;
      case 'cart_ops':
        return NotificationChannel.cartOperation;
      case 'shipping':
        return NotificationChannel.shipping;
      case 'maintenance':
        return NotificationChannel.maintenance;
      case 'user_actions':
        return NotificationChannel.userActions;
      case 'system':
        return NotificationChannel.system;
      default:
        return null;
    }
  }

  @override
  Future<void> handleBackgroundMessage() {
    return _firebaseMessaging.setForegroundNotificationPresentationOptions(
      alert: true,
      badge: true,
      sound: true,
    );
  }
}
