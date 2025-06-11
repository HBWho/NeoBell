import 'package:equatable/equatable.dart';
import 'device_user.dart';

class Device extends Equatable {
  final String sbcId;
  final String deviceFriendlyName;
  final String roleOnDevice;
  final String status;
  final String? firmwareVersion;
  final String? ownerUserId;
  final DateTime? registeredAt;
  final List<DeviceUser>? users;

  const Device({
    required this.sbcId,
    required this.deviceFriendlyName,
    required this.roleOnDevice,
    required this.status,
    this.firmwareVersion,
    this.ownerUserId,
    this.registeredAt,
    this.users,
  });

  bool get isActive => status.toLowerCase() == 'active';
  bool get isOwner => roleOnDevice.toLowerCase() == 'owner';

  // Método para criar uma cópia com usuários atualizados
  Device copyWithUsers(List<DeviceUser> users) {
    return Device(
      sbcId: sbcId,
      deviceFriendlyName: deviceFriendlyName,
      roleOnDevice: roleOnDevice,
      firmwareVersion: firmwareVersion,
      status: status,
      ownerUserId: ownerUserId,
      registeredAt: registeredAt,
      users: users,
    );
  }

  // Método para criar uma cópia com dados atualizados
  Device copyWith({
    String? deviceFriendlyName,
    String? roleOnDevice,
    String? status,
    String? firmwareVersion,
    String? ownerUserId,
    DateTime? registeredAt,
    List<DeviceUser>? users,
  }) {
    return Device(
      sbcId: sbcId,
      deviceFriendlyName: deviceFriendlyName ?? this.deviceFriendlyName,
      roleOnDevice: roleOnDevice ?? this.roleOnDevice,
      status: status ?? this.status,
      firmwareVersion: firmwareVersion ?? this.firmwareVersion,
      ownerUserId: ownerUserId ?? this.ownerUserId,
      registeredAt: registeredAt ?? this.registeredAt,
      users: users ?? this.users,
    );
  }

  @override
  List<Object?> get props => [
    sbcId,
    deviceFriendlyName,
    roleOnDevice,
    firmwareVersion,
    status,
    ownerUserId,
    registeredAt,
    users,
  ];
}
