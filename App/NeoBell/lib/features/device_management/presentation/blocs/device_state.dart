part of 'device_bloc.dart';

abstract class DeviceState extends Equatable {
  final List<Device> devices;
  final Device? currentDevice;

  const DeviceState({this.devices = const [], this.currentDevice});

  @override
  List<Object?> get props => [devices, currentDevice];
}

class DeviceInitial extends DeviceState {}

class DeviceLoading extends DeviceState {
  const DeviceLoading({super.devices, super.currentDevice});
}

class DeviceLoaded extends DeviceState {
  final String? lastEvaluatedKey;

  const DeviceLoaded({
    required super.devices,
    super.currentDevice,
    this.lastEvaluatedKey,
  });

  @override
  List<Object?> get props => [devices, currentDevice, lastEvaluatedKey];
}

class DeviceDetailsLoaded extends DeviceState {
  const DeviceDetailsLoaded({required Device device, super.devices})
    : super(currentDevice: device);
}

class DeviceUsersLoaded extends DeviceState {
  final String sbcId;

  const DeviceUsersLoaded({
    required this.sbcId,
    required super.devices,
    super.currentDevice,
  });

  @override
  List<Object?> get props => [sbcId, devices, currentDevice];
}

class DeviceOperationSuccess extends DeviceState {
  final String message;

  const DeviceOperationSuccess({
    required this.message,
    super.devices,
    super.currentDevice,
  });

  @override
  List<Object?> get props => [message, devices, currentDevice];
}

class DeviceFailure extends DeviceState {
  final String message;

  const DeviceFailure({
    required this.message,
    super.devices,
    super.currentDevice,
  });

  @override
  List<Object?> get props => [message, devices, currentDevice];
}
