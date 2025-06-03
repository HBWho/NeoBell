import '../../domain/repositories/device_repository.dart';

class DeviceUserModel extends DeviceUser {
  const DeviceUserModel({
    required String userId,
    required String email,
    required String name,
    required String role,
    required DateTime accessGrantedAt,
  }) : super(
          userId: userId,
          email: email,
          name: name,
          role: role,
          accessGrantedAt: accessGrantedAt,
        );

  factory DeviceUserModel.fromJson(Map<String, dynamic> json) {
    return DeviceUserModel(
      userId: json['user_id'],
      email: json['email'],
      name: json['name'],
      role: json['role'],
      accessGrantedAt: DateTime.parse(json['access_granted_at']),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'user_id': userId,
      'email': email,
      'name': name,
      'role': role,
      'access_granted_at': accessGrantedAt.toIso8601String(),
    };
  }
}
