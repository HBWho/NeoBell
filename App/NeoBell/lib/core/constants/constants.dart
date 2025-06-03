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
  user(AppServices.values);

  final List<AppServices> permissions;
  const UserRoles(this.permissions);
}

enum AppServices {
  // NeoBell 6 main screens
  allActivities('Ver Todas Atividades', '/home/all-activities', Icons.list_alt),
  deliveryPage(
    'Página de Entregas',
    '/home/delivery-page',
    Icons.local_shipping,
  ),
  notificationVisitor(
    'Notificações de Visitantes',
    '/home/visitor-notifications',
    Icons.video_call,
  ),
  registeredMembers(
    'Membros Registrados',
    '/home/registered-members',
    Icons.people,
  ),
  nfcRegister('Registro NFC', '/home/nfc-register', Icons.nfc),
  createDelivery('Criar Entrega', '/home/create-delivery', Icons.add_box),

  profilePage('Perfil', '/home/profile', Icons.person);

  final String name;
  final String path;
  final IconData icon;

  const AppServices(this.name, this.path, this.icon);
}

class AssetsConstants {
  static const String logo = 'assets/icon/app_icon.png';
}
