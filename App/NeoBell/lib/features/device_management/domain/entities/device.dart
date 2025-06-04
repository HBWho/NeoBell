import 'package:equatable/equatable.dart';
import 'device_user.dart';

class Device extends Equatable {
  final String sbcId;
  final String deviceFriendlyName;
  final String roleOnDevice;
  final String status;
  final DateTime lastSeen;
  final String? firmwareVersion;
  final String? ownerUserId;
  final DateTime? registeredAt;
  final NetworkInfo? networkInfo;
  final List<DeviceUser>? users; // Nova propriedade para cache de usuários

  const Device({
    required this.sbcId,
    required this.deviceFriendlyName,
    required this.roleOnDevice,
    required this.status,
    required this.lastSeen,
    this.firmwareVersion,
    this.ownerUserId,
    this.registeredAt,
    this.networkInfo,
    this.users,
  });

  bool get isOnline => status.toLowerCase() == 'online';
  bool get isOwner => roleOnDevice.toLowerCase() == 'owner';

  // Método para criar uma cópia com usuários atualizados
  Device copyWithUsers(List<DeviceUser> users) {
    return Device(
      sbcId: sbcId,
      deviceFriendlyName: deviceFriendlyName,
      roleOnDevice: roleOnDevice,
      status: status,
      lastSeen: lastSeen,
      firmwareVersion: firmwareVersion,
      ownerUserId: ownerUserId,
      registeredAt: registeredAt,
      networkInfo: networkInfo,
      users: users,
    );
  }

  // Método para criar uma cópia com dados atualizados
  Device copyWith({
    String? deviceFriendlyName,
    String? roleOnDevice,
    String? status,
    DateTime? lastSeen,
    String? firmwareVersion,
    String? ownerUserId,
    DateTime? registeredAt,
    NetworkInfo? networkInfo,
    List<DeviceUser>? users,
  }) {
    return Device(
      sbcId: sbcId,
      deviceFriendlyName: deviceFriendlyName ?? this.deviceFriendlyName,
      roleOnDevice: roleOnDevice ?? this.roleOnDevice,
      status: status ?? this.status,
      lastSeen: lastSeen ?? this.lastSeen,
      firmwareVersion: firmwareVersion ?? this.firmwareVersion,
      ownerUserId: ownerUserId ?? this.ownerUserId,
      registeredAt: registeredAt ?? this.registeredAt,
      networkInfo: networkInfo ?? this.networkInfo,
      users: users ?? this.users,
    );
  }

  @override
  List<Object?> get props => [
    sbcId,
    deviceFriendlyName,
    roleOnDevice,
    status,
    lastSeen,
    firmwareVersion,
    ownerUserId,
    registeredAt,
    networkInfo,
    users,
  ];
}

class NetworkInfo extends Equatable {
  final String? ipAddress;
  final String? wifiSsid;
  final int? signalStrength;

  const NetworkInfo({this.ipAddress, this.wifiSsid, this.signalStrength});

  @override
  List<Object?> get props => [ipAddress, wifiSsid, signalStrength];
}
