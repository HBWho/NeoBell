import 'package:equatable/equatable.dart';

class Device extends Equatable {
  final String sbcId;
  final String ownerUserId;
  final String deviceFriendlyName;
  final String userRoleOnDevice;
  final String status;
  final String? firmwareVersion;
  final DateTime registeredAt;
  final DateTime lastSeen;
  final NetworkInfo? networkInfo;

  const Device({
    required this.sbcId,
    required this.ownerUserId,
    required this.deviceFriendlyName,
    required this.userRoleOnDevice,
    required this.status,
    this.firmwareVersion,
    required this.registeredAt,
    required this.lastSeen,
    this.networkInfo,
  });

  @override
  List<Object?> get props => [
        sbcId,
        ownerUserId,
        deviceFriendlyName,
        userRoleOnDevice,
        status,
        firmwareVersion,
        registeredAt,
        lastSeen,
        networkInfo,
      ];
}

class NetworkInfo extends Equatable {
  final String ipAddress;
  final String wifiSsid;
  final int signalStrength;

  const NetworkInfo({
    required this.ipAddress,
    required this.wifiSsid,
    required this.signalStrength,
  });

  @override
  List<Object> get props => [ipAddress, wifiSsid, signalStrength];
}
