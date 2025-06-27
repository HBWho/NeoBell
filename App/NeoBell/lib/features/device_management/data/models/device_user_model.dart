import 'package:neobell/core/utils/date_formatter_utils.dart';

import '../../domain/entities/device_user.dart';

class DeviceUserModel extends DeviceUser {
  const DeviceUserModel({
    required super.userId,
    required super.name,
    required super.email,
    required super.role,
    required super.accessGrantedAt,
  });

  factory DeviceUserModel.fromJson(Map<String, dynamic> json) {
    return DeviceUserModel(
      userId: json['user_id'] as String,
      name: json['name'] as String,
      email: json['email'] as String,
      role: json['role'] as String,
      accessGrantedAt: parseApiTimestamp(json['access_granted_at']),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'user_id': userId,
      'name': name,
      'email': email,
      'role': role,
      'access_granted_at': accessGrantedAt.toIso8601String(),
    };
  }

  factory DeviceUserModel.fromEntity(DeviceUser deviceUser) {
    return DeviceUserModel(
      userId: deviceUser.userId,
      name: deviceUser.name,
      email: deviceUser.email,
      role: deviceUser.role,
      accessGrantedAt: deviceUser.accessGrantedAt,
    );
  }
}
