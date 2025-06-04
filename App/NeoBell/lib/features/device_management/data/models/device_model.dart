import '../../domain/entities/device.dart';
import '../../domain/entities/device_user.dart';
import 'device_user_model.dart';

class DeviceModel extends Device {
  const DeviceModel({
    required super.sbcId,
    required super.deviceFriendlyName,
    required super.roleOnDevice,
    required super.status,
    required super.lastSeen,
    super.firmwareVersion,
    super.ownerUserId,
    super.registeredAt,
    super.networkInfo,
    super.users,
  });

  factory DeviceModel.fromJson(Map<String, dynamic> json) {
    return DeviceModel(
      sbcId: json['sbc_id'] as String,
      deviceFriendlyName: json['device_friendly_name'] as String,
      roleOnDevice:
          json['role_on_device'] as String? ??
          json['user_role_on_device'] as String? ??
          'Resident',
      status: json['status'] as String,
      lastSeen: DateTime.parse(json['last_seen'] as String),
      firmwareVersion: json['firmware_version'] as String?,
      ownerUserId: json['owner_user_id'] as String?,
      registeredAt:
          json['registered_at'] != null
              ? DateTime.parse(json['registered_at'] as String)
              : null,
      networkInfo:
          json['network_info'] != null
              ? NetworkInfoModel.fromJson(
                json['network_info'] as Map<String, dynamic>,
              )
              : null,
      users:
          json['users'] != null
              ? (json['users'] as List<dynamic>)
                  .map(
                    (user) =>
                        DeviceUserModel.fromJson(user as Map<String, dynamic>),
                  )
                  .toList()
              : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'sbc_id': sbcId,
      'device_friendly_name': deviceFriendlyName,
      'role_on_device': roleOnDevice,
      'status': status,
      'last_seen': lastSeen.toIso8601String(),
      if (firmwareVersion != null) 'firmware_version': firmwareVersion,
      if (ownerUserId != null) 'owner_user_id': ownerUserId,
      if (registeredAt != null)
        'registered_at': registeredAt!.toIso8601String(),
      if (networkInfo != null)
        'network_info': (networkInfo as NetworkInfoModel).toJson(),
      if (users != null)
        'users':
            users!.map((user) => (user as DeviceUserModel).toJson()).toList(),
    };
  }

  factory DeviceModel.fromEntity(Device device) {
    return DeviceModel(
      sbcId: device.sbcId,
      deviceFriendlyName: device.deviceFriendlyName,
      roleOnDevice: device.roleOnDevice,
      status: device.status,
      lastSeen: device.lastSeen,
      firmwareVersion: device.firmwareVersion,
      ownerUserId: device.ownerUserId,
      registeredAt: device.registeredAt,
      networkInfo: device.networkInfo,
      users: device.users,
    );
  }

  @override
  DeviceModel copyWithUsers(List<DeviceUser> users) {
    return DeviceModel(
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

  @override
  DeviceModel copyWith({
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
    return DeviceModel(
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
}

class NetworkInfoModel extends NetworkInfo {
  const NetworkInfoModel({
    super.ipAddress,
    super.wifiSsid,
    super.signalStrength,
  });

  factory NetworkInfoModel.fromJson(Map<String, dynamic> json) {
    return NetworkInfoModel(
      ipAddress: json['ip_address'] as String?,
      wifiSsid: json['wifi_ssid'] as String?,
      signalStrength: json['signal_strength'] as int?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      if (ipAddress != null) 'ip_address': ipAddress,
      if (wifiSsid != null) 'wifi_ssid': wifiSsid,
      if (signalStrength != null) 'signal_strength': signalStrength,
    };
  }
}
