import 'package:neobell/core/utils/date_formatter_utils.dart';

import '../../domain/entities/device.dart';
import '../../domain/entities/device_user.dart';
import 'device_user_model.dart';

class DeviceModel extends Device {
  const DeviceModel({
    required super.sbcId,
    required super.deviceFriendlyName,
    required super.roleOnDevice,
    required super.status,
    super.firmwareVersion,
    super.ownerUserId,
    super.registeredAt,
    super.users,
  });

  factory DeviceModel.fromJson(Map<String, dynamic> json) {
    return DeviceModel(
      sbcId: json['sbc_id'] as String,
      deviceFriendlyName: json['device_friendly_name'] as String,
      status: json['status'] as String,
      roleOnDevice:
          json['role_on_device'] as String? ??
          json['user_role_on_device'] as String? ??
          'Resident',
      firmwareVersion: json['firmware_version'] as String?,
      ownerUserId: json['owner_user_id'] as String?,
      registeredAt: parseApiTimestamp(json['registered_at']),
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
      if (firmwareVersion != null) 'firmware_version': firmwareVersion,
      if (ownerUserId != null) 'owner_user_id': ownerUserId,
      if (registeredAt != null)
        'registered_at': registeredAt!.toIso8601String(),
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
      firmwareVersion: device.firmwareVersion,
      status: device.status,
      ownerUserId: device.ownerUserId,
      registeredAt: device.registeredAt,
      users: device.users,
    );
  }

  @override
  DeviceModel copyWithUsers(List<DeviceUser> users) {
    return DeviceModel(
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

  @override
  DeviceModel copyWith({
    String? deviceFriendlyName,
    String? roleOnDevice,
    String? status,
    String? firmwareVersion,
    String? ownerUserId,
    DateTime? registeredAt,
    List<DeviceUser>? users,
  }) {
    return DeviceModel(
      sbcId: sbcId,
      deviceFriendlyName: deviceFriendlyName ?? this.deviceFriendlyName,
      roleOnDevice: roleOnDevice ?? this.roleOnDevice,
      firmwareVersion: firmwareVersion ?? this.firmwareVersion,
      status: status ?? this.status,
      ownerUserId: ownerUserId ?? this.ownerUserId,
      registeredAt: registeredAt ?? this.registeredAt,
      users: users ?? this.users,
    );
  }
}
