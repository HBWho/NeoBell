import '../../domain/entities/device.dart';

class DeviceModel extends Device {
  const DeviceModel({
    required super.sbcId,
    required super.ownerUserId,
    required super.deviceFriendlyName,
    required super.userRoleOnDevice,
    required super.status,
    super.firmwareVersion,
    required super.registeredAt,
    required super.lastSeen,
    NetworkInfoModel? super.networkInfo,
  });

  factory DeviceModel.fromJson(Map<String, dynamic> json) {
    return DeviceModel(
      sbcId: json['sbc_id'],
      ownerUserId: json['owner_user_id'],
      deviceFriendlyName: json['device_friendly_name'],
      userRoleOnDevice: json['user_role_on_device'],
      status: json['status'],
      firmwareVersion: json['firmware_version'],
      registeredAt: DateTime.parse(json['registered_at']),
      lastSeen: DateTime.parse(json['last_seen']),
      networkInfo:
          json['network_info'] != null
              ? NetworkInfoModel.fromJson(json['network_info'])
              : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'sbc_id': sbcId,
      'owner_user_id': ownerUserId,
      'device_friendly_name': deviceFriendlyName,
      'user_role_on_device': userRoleOnDevice,
      'status': status,
      'firmware_version': firmwareVersion,
      'registered_at': registeredAt.toIso8601String(),
      'last_seen': lastSeen.toIso8601String(),
      'network_info':
          networkInfo != null
              ? (networkInfo as NetworkInfoModel).toJson()
              : null,
    };
  }
}

class NetworkInfoModel extends NetworkInfo {
  const NetworkInfoModel({
    required super.ipAddress,
    required super.wifiSsid,
    required super.signalStrength,
  });

  factory NetworkInfoModel.fromJson(Map<String, dynamic> json) {
    return NetworkInfoModel(
      ipAddress: json['ip_address'],
      wifiSsid: json['wifi_ssid'],
      signalStrength: json['signal_strength'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'ip_address': ipAddress,
      'wifi_ssid': wifiSsid,
      'signal_strength': signalStrength,
    };
  }
}
