part of 'device_bloc.dart';

abstract class DeviceEvent extends Equatable {
  const DeviceEvent();

  @override
  List<Object?> get props => [];
}

class LoadDevices extends DeviceEvent {
  final int? limit;
  final String? lastEvaluatedKey;

  const LoadDevices({this.limit, this.lastEvaluatedKey});

  @override
  List<Object?> get props => [limit, lastEvaluatedKey];
}

class RefreshDevices extends DeviceEvent {}

class LoadDeviceDetails extends DeviceEvent {
  final String sbcId;

  const LoadDeviceDetails(this.sbcId);

  @override
  List<Object> get props => [sbcId];
}

class UpdateDeviceEvent extends DeviceEvent {
  final String sbcId;
  final String deviceFriendlyName;

  const UpdateDeviceEvent({
    required this.sbcId,
    required this.deviceFriendlyName,
  });

  @override
  List<Object> get props => [sbcId, deviceFriendlyName];
}

class DeleteDeviceEvent extends DeviceEvent {
  final String sbcId;

  const DeleteDeviceEvent(this.sbcId);

  @override
  List<Object> get props => [sbcId];
}

class LoadDeviceUsers extends DeviceEvent {
  final String sbcId;

  const LoadDeviceUsers(this.sbcId);

  @override
  List<Object> get props => [sbcId];
}

class AddDeviceUserEvent extends DeviceEvent {
  final String sbcId;
  final String userEmail;

  const AddDeviceUserEvent({required this.sbcId, required this.userEmail});

  @override
  List<Object> get props => [sbcId, userEmail];
}

class RemoveDeviceUserEvent extends DeviceEvent {
  final String sbcId;
  final String userId;

  const RemoveDeviceUserEvent({required this.sbcId, required this.userId});

  @override
  List<Object> get props => [sbcId, userId];
}
