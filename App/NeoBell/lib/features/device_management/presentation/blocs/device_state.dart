part of 'device_bloc.dart';

@immutable
sealed class DeviceState {}

final class DeviceInitial extends DeviceState {}

final class DeviceLoading extends DeviceState {}

final class DeviceSuccess extends DeviceState {
  final List<Device> devices;
  DeviceSuccess(this.devices);
}

final class DeviceDetailsLoaded extends DeviceState {
  final Device device;
  DeviceDetailsLoaded(this.device);
}

final class DeviceUsersLoaded extends DeviceState {
  final List<DeviceUser> users;
  final String deviceId;
  DeviceUsersLoaded(this.users, this.deviceId);
}

final class DeviceOperationSuccess extends DeviceState {
  final String message;
  DeviceOperationSuccess(this.message);
}

final class DeviceFailure extends DeviceState {
  final String message;
  DeviceFailure(this.message);
}
