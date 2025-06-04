import 'package:equatable/equatable.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:logger/logger.dart';
import '../../domain/entities/device.dart';
import '../../domain/use_cases/get_devices.dart';
import '../../domain/use_cases/get_device_details.dart';
import '../../domain/use_cases/update_device.dart';
import '../../domain/use_cases/get_device_users.dart';
import '../../domain/use_cases/add_device_user.dart';
import '../../domain/use_cases/remove_device_user.dart';

part 'device_event.dart';
part 'device_state.dart';

class DeviceBloc extends Bloc<DeviceEvent, DeviceState> {
  final GetDevices _getDevices;
  final GetDeviceDetails _getDeviceDetails;
  final UpdateDevice _updateDevice;
  final GetDeviceUsers _getDeviceUsers;
  final AddDeviceUser _addDeviceUser;
  final RemoveDeviceUser _removeDeviceUser;

  static final _logger = Logger();

  DeviceBloc({
    required GetDevices getDevices,
    required GetDeviceDetails getDeviceDetails,
    required UpdateDevice updateDevice,
    required GetDeviceUsers getDeviceUsers,
    required AddDeviceUser addDeviceUser,
    required RemoveDeviceUser removeDeviceUser,
  }) : _getDevices = getDevices,
       _getDeviceDetails = getDeviceDetails,
       _updateDevice = updateDevice,
       _getDeviceUsers = getDeviceUsers,
       _addDeviceUser = addDeviceUser,
       _removeDeviceUser = removeDeviceUser,
       super(DeviceInitial()) {
    on<LoadDevices>(_onLoadDevices);
    on<RefreshDevices>(_onRefreshDevices);
    on<LoadDeviceDetails>(_onLoadDeviceDetails);
    on<UpdateDeviceEvent>(_onUpdateDevice);
    on<LoadDeviceUsers>(_onLoadDeviceUsers);
    on<AddDeviceUserEvent>(_onAddDeviceUser);
    on<RemoveDeviceUserEvent>(_onRemoveDeviceUser);
  }

  Future<void> _onLoadDevices(
    LoadDevices event,
    Emitter<DeviceState> emit,
  ) async {
    emit(
      DeviceLoading(devices: state.devices, currentDevice: state.currentDevice),
    );

    final result = await _getDevices(
      GetDevicesParams(
        limit: event.limit,
        lastEvaluatedKey: event.lastEvaluatedKey,
      ),
    );

    result.fold(
      (failure) => emit(
        DeviceFailure(
          message: failure.message,
          devices: state.devices,
          currentDevice: state.currentDevice,
        ),
      ),
      (devices) => emit(
        DeviceLoaded(
          devices: devices,
          currentDevice: state.currentDevice,
          lastEvaluatedKey: event.lastEvaluatedKey,
        ),
      ),
    );
  }

  Future<void> _onRefreshDevices(
    RefreshDevices event,
    Emitter<DeviceState> emit,
  ) async {
    emit(DeviceLoading());
    final result = await _getDevices(GetDevicesParams());

    result.fold(
      (failure) => emit(DeviceFailure(message: failure.message)),
      (devices) => emit(DeviceLoaded(devices: devices)),
    );
  }

  Future<void> _onLoadDeviceDetails(
    LoadDeviceDetails event,
    Emitter<DeviceState> emit,
  ) async {
    final cachedDevice =
        state.devices
            .where((device) => device.sbcId == event.sbcId)
            .firstOrNull;
    if (cachedDevice != null && cachedDevice.firmwareVersion != null) {
      emit(DeviceDetailsLoaded(device: cachedDevice, devices: state.devices));
      return;
    }

    emit(
      DeviceLoading(devices: state.devices, currentDevice: state.currentDevice),
    );

    final result = await _getDeviceDetails(
      GetDeviceDetailsParams(sbcId: event.sbcId),
    );

    result.fold(
      (failure) => emit(
        DeviceFailure(
          message: failure.message,
          devices: state.devices,
          currentDevice: state.currentDevice,
        ),
      ),
      (device) {
        List<Device> updatedDevices =
            state.devices
                .map((d) => d.sbcId == device.sbcId ? device : d)
                .toList();
        if (!updatedDevices.any((d) => d.sbcId == device.sbcId)) {
          updatedDevices.add(device);
        }
        emit(DeviceDetailsLoaded(device: device, devices: updatedDevices));
      },
    );
  }

  Future<void> _onUpdateDevice(
    UpdateDeviceEvent event,
    Emitter<DeviceState> emit,
  ) async {
    emit(
      DeviceLoading(devices: state.devices, currentDevice: state.currentDevice),
    );

    final result = await _updateDevice(
      UpdateDeviceParams(
        sbcId: event.sbcId,
        deviceFriendlyName: event.deviceFriendlyName,
      ),
    );

    result.fold(
      (failure) => emit(
        DeviceFailure(
          message: failure.message,
          devices: state.devices,
          currentDevice: state.currentDevice,
        ),
      ),
      (updatedDevice) {
        final updatedDevices =
            state.devices.map((device) {
              if (device.sbcId == updatedDevice.sbcId) {
                return device.copyWith(
                  deviceFriendlyName: updatedDevice.deviceFriendlyName,
                );
              }
              return device;
            }).toList();

        final newCurrentDevice =
            state.currentDevice?.sbcId == updatedDevice.sbcId
                ? state.currentDevice!.copyWith(
                  deviceFriendlyName: updatedDevice.deviceFriendlyName,
                )
                : state.currentDevice;

        emit(
          DeviceOperationSuccess(
            message: 'Device updated successfully',
            devices: updatedDevices,
            currentDevice: newCurrentDevice,
          ),
        );
      },
    );
  }

  Future<void> _onLoadDeviceUsers(
    LoadDeviceUsers event,
    Emitter<DeviceState> emit,
  ) async {
    final cachedDevice =
        state.devices
            .where((device) => device.sbcId == event.sbcId)
            .firstOrNull;

    if (cachedDevice?.users != null) {
      emit(
        DeviceUsersLoaded(
          sbcId: event.sbcId,
          devices: state.devices,
          currentDevice: state.currentDevice,
        ),
      );
      return;
    }

    emit(
      DeviceLoading(devices: state.devices, currentDevice: state.currentDevice),
    );

    final result = await _getDeviceUsers(
      GetDeviceUsersParams(sbcId: event.sbcId),
    );

    result.fold(
      (failure) => emit(
        DeviceFailure(
          message: failure.message,
          devices: state.devices,
          currentDevice: state.currentDevice,
        ),
      ),
      (users) {
        final updatedDevices =
            state.devices.map((device) {
              if (device.sbcId == event.sbcId) {
                return device.copyWithUsers(users);
              }
              return device;
            }).toList();
        final newCurrentDevice =
            state.currentDevice?.sbcId == event.sbcId
                ? state.currentDevice!.copyWithUsers(users)
                : state.currentDevice;
        emit(
          DeviceUsersLoaded(
            sbcId: event.sbcId,
            devices: updatedDevices,
            currentDevice: newCurrentDevice,
          ),
        );
      },
    );
  }

  Future<void> _onAddDeviceUser(
    AddDeviceUserEvent event,
    Emitter<DeviceState> emit,
  ) async {
    emit(
      DeviceLoading(devices: state.devices, currentDevice: state.currentDevice),
    );

    final result = await _addDeviceUser(
      AddDeviceUserParams(sbcId: event.sbcId, userEmail: event.userEmail),
    );

    result.fold(
      (failure) => emit(
        DeviceFailure(
          message: failure.message,
          devices: state.devices,
          currentDevice: state.currentDevice,
        ),
      ),
      (_) {
        _logger.i('Added user ${event.userEmail} to device ${event.sbcId}');

        final updatedDevices =
            state.devices.map((device) {
              if (device.sbcId == event.sbcId) {
                return device.copyWith(users: null);
              }
              return device;
            }).toList();

        final newCurrentDevice =
            state.currentDevice?.sbcId == event.sbcId
                ? state.currentDevice!.copyWith(users: null)
                : state.currentDevice;

        emit(
          DeviceOperationSuccess(
            message: 'User added successfully',
            devices: updatedDevices,
            currentDevice: newCurrentDevice,
          ),
        );

        // Recarregar usuários
        add(LoadDeviceUsers(event.sbcId));
      },
    );
  }

  Future<void> _onRemoveDeviceUser(
    RemoveDeviceUserEvent event,
    Emitter<DeviceState> emit,
  ) async {
    emit(
      DeviceLoading(devices: state.devices, currentDevice: state.currentDevice),
    );

    final result = await _removeDeviceUser(
      RemoveDeviceUserParams(sbcId: event.sbcId, userId: event.userId),
    );

    result.fold(
      (failure) => emit(
        DeviceFailure(
          message: failure.message,
          devices: state.devices,
          currentDevice: state.currentDevice,
        ),
      ),
      (_) {
        // Remover usuário do cache local
        final updatedDevices =
            state.devices.map((device) {
              if (device.sbcId == event.sbcId && device.users != null) {
                final updatedUsers =
                    device.users!
                        .where((user) => user.userId != event.userId)
                        .toList();
                return device.copyWithUsers(updatedUsers);
              }
              return device;
            }).toList();

        final newCurrentDevice =
            state.currentDevice?.sbcId == event.sbcId &&
                    state.currentDevice?.users != null
                ? state.currentDevice!.copyWithUsers(
                  state.currentDevice!.users!
                      .where((user) => user.userId != event.userId)
                      .toList(),
                )
                : state.currentDevice;

        emit(
          DeviceOperationSuccess(
            message: 'User removed successfully',
            devices: updatedDevices,
            currentDevice: newCurrentDevice,
          ),
        );
      },
    );
  }
}
