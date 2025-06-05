enum NotificationChannel {
  packageDelivery(
    'package_delivery',
    'Package Delivery',
    'Notifications related to package delivery status',
  ),
  videoMessages(
    'video_messages',
    'Video Messages',
    'Notifications for new video messages',
  ),
  deviceManagement(
    'device_management',
    'Device Management',
    'Notifications for device management updates',
  ),
  userActions(
    'user_actions',
    'User Actions',
    'User authentication and permission updates',
  ),
  visitorRegistration(
    'visitor_registration',
    'Visitor Registration',
    'Notifications for visitor registration and permissions',
  ),
  system('system', 'System', 'Critical system notifications');

  final String id;
  final String name;
  final String description;

  const NotificationChannel(this.id, this.name, this.description);
}
