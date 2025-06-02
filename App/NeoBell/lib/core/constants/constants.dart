import 'package:flutter/material.dart';

class MainConstants {
  static const String appName = 'NeoBell';
}

class AuthConstants {
  static const int minPasswordLength = 3;
}

enum DataKeys { apiUrl, savePassword }

enum UserRoles {
  admin(AppServices.values),
  user(AppServices.values),
  ;

  final List<AppServices> permissions;
  const UserRoles(this.permissions);
}

enum AppServices {
  updateProfile('Perfil', '/home/changeprofile', Icons.person),
  fetchRecords('Registros', '/home/records', Icons.receipt_long);

  final String name;
  final String path;
  final IconData icon;

  const AppServices(this.name, this.path, this.icon);
}

class AssetsConstants {
  static const String logo = 'assets/icon/app_icon.png';
}
