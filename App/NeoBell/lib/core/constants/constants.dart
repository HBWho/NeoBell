import 'package:flutter/material.dart';

class MainConstants {
  static const String appName = 'NeoBell';
}

enum AppServices {
  // NeoBell 6 main screens
  logs('Logs', '/home/activity-logs', Icons.list_alt),
  deliveryPage('Delivery Page', '/home/delivery-page', Icons.local_shipping),
  visitorPermissions(
    'Visitor Permissions',
    '/home/visitor-permissions',
    Icons.assignment_ind,
  ),
  videoMessages('Video Messages', '/home/video-messages', Icons.video_call),
  registeredMembers(
    'Registered Members',
    '/home/registered-members',
    Icons.people,
  ),
  nfc('NFC', '/home/nfc', Icons.nfc),
  createDelivery('Create Delivery', '/home/create-delivery', Icons.add_box),
  profilePage('Profile', '/home/profile', Icons.person);

  final String name;
  final String path;
  final IconData icon;

  const AppServices(this.name, this.path, this.icon);
}

class AssetsConstants {
  static const String logo = 'assets/icon/app_icon.png';
}
