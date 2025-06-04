part of 'device_bloc.dart';

@immutable
abstract class DeviceState extends Equatable {
  const DeviceState();

  @override
  List<Object?> get props => [];
}

class DeviceInitial extends DeviceState {}

class DeviceLoading extends DeviceState {}

class DeviceSuccess extends DeviceState {
  final List<Device> devices;

  const DeviceSuccess(this.devices);

  @override
  List<Object> get props => [devices];
}

class DeviceDetailsLoaded extends DeviceState {
  final Device device;

  const DeviceDetailsLoaded(this.device);

  @override
  List<Object> get props => [device];
}

class DeviceUsersLoaded extends DeviceState {
  final List<DeviceUser> users;
  final String deviceId;

  const DeviceUsersLoaded(this.users, this.deviceId);

  @override
  List<Object> get props => [users, deviceId];
}

class DeviceOperationSuccess extends DeviceState {
  final String message;

  const DeviceOperationSuccess(this.message);

  @override
  List<Object> get props => [message];
}

class DeviceFailure extends DeviceState {
  final String message;

  const DeviceFailure(this.message);

  @override
  List<Object> get props => [message];
}
