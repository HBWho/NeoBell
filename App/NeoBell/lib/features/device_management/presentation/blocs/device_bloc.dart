import 'package:equatable/equatable.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:logger/logger.dart';
import '../../domain/entities/device.dart';
import '../../domain/repositories/device_repository.dart';
import '../../domain/use_cases/add_device_user.dart';
import '../../domain/use_cases/get_device_details.dart';
import '../../domain/use_cases/get_devices.dart';
import '../../domain/use_cases/get_device_users.dart';
import '../../domain/use_cases/remove_device_user.dart';
import '../../domain/use_cases/update_device_details.dart';
import '../../../../core/usecase/usecase.dart';

part 'device_event.dart';
part 'device_state.dart';

class DeviceBloc extends Bloc<DeviceEvent, DeviceState> {
  final Logger _logger = Logger();
  final GetDevices _getDevices;
  final GetDeviceDetails _getDeviceDetails;
  final UpdateDeviceDetails _updateDeviceDetails;
  final GetDeviceUsers _getDeviceUsers;
  final AddDeviceUser _addDeviceUser;
  final RemoveDeviceUser _removeDeviceUser;

  DeviceBloc({
    required GetDevices getDevices,
    required GetDeviceDetails getDeviceDetails,
    required UpdateDeviceDetails updateDeviceDetails,
    required GetDeviceUsers getDeviceUsers,
    required AddDeviceUser addDeviceUser,
    required RemoveDeviceUser removeDeviceUser,
  }) : _getDevices = getDevices,
       _getDeviceDetails = getDeviceDetails,
       _updateDeviceDetails = updateDeviceDetails,
       _getDeviceUsers = getDeviceUsers,
       _addDeviceUser = addDeviceUser,
       _removeDeviceUser = removeDeviceUser,
       super(DeviceInitial()) {
    on<LoadDevices>(_onLoadDevices);
    on<LoadDeviceDetails>(_onLoadDeviceDetails);
    on<UpdateDevice>(_onUpdateDevice);
    on<LoadDeviceUsers>(_onLoadDeviceUsers);
    on<AddUserToDevice>(_onAddUserToDevice);
    on<RemoveUserFromDevice>(_onRemoveUserFromDevice);
  }

  Future<void> _onLoadDevices(
    LoadDevices event,
    Emitter<DeviceState> emit,
  ) async {
    emit(DeviceLoading());
    final result = await _getDevices(NoParams());
    result.fold((failure) => emit(DeviceFailure(failure.message)), (devices) {
      _logger.i('Loaded ${devices.length} devices');
      emit(DeviceSuccess(devices));
    });
  }

  Future<void> _onLoadDeviceDetails(
    LoadDeviceDetails event,
    Emitter<DeviceState> emit,
  ) async {
    emit(DeviceLoading());
    final result = await _getDeviceDetails(event.sbcId);
    result.fold((failure) => emit(DeviceFailure(failure.message)), (device) {
      _logger.i('Loaded device details for ${device.sbcId}');
      emit(DeviceDetailsLoaded(device));
    });
  }

  Future<void> _onUpdateDevice(
    UpdateDevice event,
    Emitter<DeviceState> emit,
  ) async {
    emit(DeviceLoading());
    final result = await _updateDeviceDetails(
      UpdateDeviceParams(sbcId: event.sbcId, newName: event.newName),
    );
    result.fold((failure) => emit(DeviceFailure(failure.message)), (device) {
      _logger.i('Updated device ${device.sbcId}');
      emit(DeviceOperationSuccess('Device updated successfully'));
    });
  }

  Future<void> _onLoadDeviceUsers(
    LoadDeviceUsers event,
    Emitter<DeviceState> emit,
  ) async {
    emit(DeviceLoading());
    final result = await _getDeviceUsers(event.sbcId);
    result.fold((failure) => emit(DeviceFailure(failure.message)), (users) {
      _logger.i('Loaded ${users.length} users for device ${event.sbcId}');
      emit(DeviceUsersLoaded(users, event.sbcId));
    });
  }

  Future<void> _onAddUserToDevice(
    AddUserToDevice event,
    Emitter<DeviceState> emit,
  ) async {
    emit(DeviceLoading());
    final result = await _addDeviceUser(
      AddDeviceUserParams(
        sbcId: event.sbcId,
        email: event.email,
        role: event.role,
      ),
    );
    result.fold((failure) => emit(DeviceFailure(failure.message)), (user) {
      _logger.i('Added user ${user.email} to device ${event.sbcId}');
      emit(DeviceOperationSuccess('User added successfully'));
    });
  }

  Future<void> _onRemoveUserFromDevice(
    RemoveUserFromDevice event,
    Emitter<DeviceState> emit,
  ) async {
    emit(DeviceLoading());
    final result = await _removeDeviceUser(
      RemoveDeviceUserParams(sbcId: event.sbcId, userId: event.userId),
    );
    result.fold((failure) => emit(DeviceFailure(failure.message)), (_) {
      _logger.i('Removed user ${event.userId} from device ${event.sbcId}');
      emit(DeviceOperationSuccess('User removed successfully'));
    });
  }
}
