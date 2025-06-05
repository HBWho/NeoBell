import '../entities/notification_message.dart';

abstract class NotificationRepository {
  Stream<Map<String, dynamic>> get onNotificationTap;
  Future<void> initialize();
  Future<void> showNotification(NotificationMessage message);
  Future<String?> getFirebaseToken();
}
