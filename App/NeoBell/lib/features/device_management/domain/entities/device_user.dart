import 'package:equatable/equatable.dart';

class DeviceUser extends Equatable {
  final String userId;
  final String name;
  final String email;
  final String role;
  final DateTime accessGrantedAt;

  const DeviceUser({
    required this.userId,
    required this.name,
    required this.email,
    required this.role,
    required this.accessGrantedAt,
  });

  @override
  List<Object> get props => [userId, name, email, role, accessGrantedAt];

  DeviceUser copyWith({
    String? userId,
    String? name,
    String? email,
    String? role,
    DateTime? accessGrantedAt,
  }) {
    return DeviceUser(
      userId: userId ?? this.userId,
      name: name ?? this.name,
      email: email ?? this.email,
      role: role ?? this.role,
      accessGrantedAt: accessGrantedAt ?? this.accessGrantedAt,
    );
  }

  bool get isOwner => role.toLowerCase() == 'owner';
}
