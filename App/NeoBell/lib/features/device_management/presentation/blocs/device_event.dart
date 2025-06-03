part of 'device_bloc.dart';

@immutable
sealed class DeviceEvent {}

final class LoadDevices extends DeviceEvent {}

final class LoadDeviceDetails extends DeviceEvent {
  final String sbcId;
  LoadDeviceDetails(this.sbcId);
}

final class UpdateDevice extends DeviceEvent {
  final String sbcId;
  final String newName;
  UpdateDevice({required this.sbcId, required this.newName});
}

final class LoadDeviceUsers extends DeviceEvent {
  final String sbcId;
  LoadDeviceUsers(this.sbcId);
}

final class AddUserToDevice extends DeviceEvent {
  final String sbcId;
  final String email;
  final String role;
  AddUserToDevice({
    required this.sbcId,
    required this.email,
    required this.role,
  });
}

final class RemoveUserFromDevice extends DeviceEvent {
  final String sbcId;
  final String userId;
  RemoveUserFromDevice({required this.sbcId, required this.userId});
}
