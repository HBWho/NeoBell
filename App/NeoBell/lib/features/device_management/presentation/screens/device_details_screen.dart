import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:neobell/core/utils/date_formatter_utils.dart';
import '../../../../core/common/widgets/base_screen_widget.dart';
import '../../../../core/utils/show_snackbar.dart';
import '../../../../core/utils/show_confimation_dialog.dart';
import '../../domain/entities/device.dart';
import '../../domain/entities/device_user.dart';
import '../blocs/device_bloc.dart';
import '../widgets/add_device_user_dialog.dart';

class DeviceDetailsScreen extends StatefulWidget {
  final String sbcId;

  const DeviceDetailsScreen({super.key, required this.sbcId});

  @override
  State<DeviceDetailsScreen> createState() => _DeviceDetailsScreenState();
}

class _DeviceDetailsScreenState extends State<DeviceDetailsScreen> {
  bool refreshing = false;
  @override
  void initState() {
    super.initState();
    _initializeDevice();
  }

  void _initializeDevice() {
    final state = context.read<DeviceBloc>().state;
    if (state is DeviceInitial) {
      context.read<DeviceBloc>().add(const LoadDevices());
    }
    context.read<DeviceBloc>().add(LoadDeviceDetails(widget.sbcId));
    context.read<DeviceBloc>().add(LoadDeviceUsers(widget.sbcId));
  }

  @override
  Widget build(BuildContext context) {
    return BlocConsumer<DeviceBloc, DeviceState>(
      listener: (context, state) {
        if (refreshing && state is DeviceLoaded) {
          refreshing = false;
          context.read<DeviceBloc>().add(LoadDeviceDetails(widget.sbcId));
          context.read<DeviceBloc>().add(LoadDeviceUsers(widget.sbcId));
          showSnackBar(
            context,
            message: 'Data refreshed successfully',
            isSucess: true,
          );
        } else if (state is DeviceFailure) {
          showSnackBar(context, message: state.message, isError: true);
        } else if (state is DeviceOperationSuccess) {
          showSnackBar(context, message: state.message, isSucess: true);
        }
      },
      builder: (context, state) {
        final device = _getDevice(state);
        if (device == null) {
          if (state is DeviceLoading) {
            return const BaseScreenWidget(
              title: 'Loading...',
              body: Center(child: CircularProgressIndicator()),
            );
          } else {
            return BaseScreenWidget(
              title: 'Device Not Found',
              body: Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const Icon(
                      Icons.error_outline,
                      size: 64,
                      color: Colors.red,
                    ),
                    const SizedBox(height: 16),
                    const Text('Device not found'),
                    const SizedBox(height: 16),
                    ElevatedButton(
                      onPressed: () => Navigator.of(context).pop(),
                      child: const Text('Voltar'),
                    ),
                  ],
                ),
              ),
            );
          }
        }

        return BaseScreenWidget(
          title: device.deviceFriendlyName,
          actions: [
            if (device.isOwner)
              IconButton(
                icon: const Icon(Icons.person_add),
                onPressed: () => _showAddUserDialog(context, device),
              ),
            IconButton(
              icon: const Icon(Icons.refresh),
              onPressed: () => _refreshData(),
            ),
          ],
          body: SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _buildDeviceInfoCard(device, state),
                const SizedBox(height: 16),
                _buildUsersSection(device, state),
              ],
            ),
          ),
        );
      },
    );
  }

  Device? _getDevice(DeviceState state) {
    if (state.currentDevice?.sbcId == widget.sbcId) {
      return state.currentDevice;
    }

    try {
      return state.devices.firstWhere((device) => device.sbcId == widget.sbcId);
    } catch (e) {
      return null;
    }
  }

  void _refreshData() {
    context.read<DeviceBloc>().add(RefreshDevices());
    refreshing = true;
  }

  Widget _buildDeviceInfoCard(Device device, DeviceState state) {
    final isLoading = state is DeviceLoading;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: device.isActive ? Colors.green : Colors.grey,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: const Icon(
                    Icons.doorbell,
                    color: Colors.white,
                    size: 32,
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Expanded(
                            child: Text(
                              device.deviceFriendlyName,
                              style: const TextStyle(
                                fontSize: 20,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ),
                          if (isLoading) ...[
                            const SizedBox(width: 8),
                            const SizedBox(
                              width: 16,
                              height: 16,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            ),
                          ],
                        ],
                      ),
                      const SizedBox(height: 4),
                      Row(
                        children: [
                          Container(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 12,
                              vertical: 4,
                            ),
                            decoration: BoxDecoration(
                              color:
                                  device.isActive ? Colors.green : Colors.grey,
                              borderRadius: BorderRadius.circular(16),
                            ),
                            child: Text(
                              device.status.toUpperCase(),
                              style: const TextStyle(
                                color: Colors.white,
                                fontSize: 12,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ),
                          const SizedBox(width: 8),
                          Container(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 12,
                              vertical: 4,
                            ),
                            decoration: BoxDecoration(
                              color:
                                  device.isOwner ? Colors.blue : Colors.orange,
                              borderRadius: BorderRadius.circular(16),
                            ),
                            child: Text(
                              device.roleOnDevice,
                              style: const TextStyle(
                                color: Colors.white,
                                fontSize: 12,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.edit),
                  onPressed: () => _showEditDeviceDialog(context, device),
                ),
              ],
            ),
            const SizedBox(height: 16),
            _buildInfoRow('Device ID', device.sbcId),
            if (device.firmwareVersion != null)
              _buildInfoRow('Firmware Version', device.firmwareVersion!),
            if (device.registeredAt != null)
              _buildInfoRow(
                'Registered At',
                formatShortTimestamp(device.registeredAt!),
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildUsersSection(Device device, DeviceState state) {
    final users = device.users ?? [];
    final isLoadingUsers = state is DeviceLoading && device.users == null;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  'Linked Users',
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                ),
                if (device.isOwner)
                  TextButton.icon(
                    onPressed: () => _showAddUserDialog(context, device),
                    icon: const Icon(Icons.person_add),
                    label: const Text('Add'),
                  ),
              ],
            ),
            const SizedBox(height: 12),
            if (isLoadingUsers)
              const Center(child: CircularProgressIndicator())
            else if (users.isEmpty)
              const Text(
                'No linked users found',
                style: TextStyle(color: Colors.grey),
              )
            else
              ListView.separated(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                itemCount: users.length,
                separatorBuilder: (context, index) => const Divider(),
                itemBuilder: (context, index) {
                  final user = users[index];
                  return _buildUserItem(user, device);
                },
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildUserItem(DeviceUser user, Device device) {
    return Column(
      children: [
        ListTile(
          leading: CircleAvatar(
            backgroundColor: user.isOwner ? Colors.blue : Colors.orange,
            child: Text(
              user.name.isNotEmpty ? user.name[0].toUpperCase() : '?',
              style: const TextStyle(
                color: Colors.white,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
          title: Text(user.name),
          subtitle: Text(user.email),
          trailing: Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
            decoration: BoxDecoration(
              color: user.isOwner ? Colors.blue : Colors.orange,
              borderRadius: BorderRadius.circular(12),
            ),
            child: Text(
              user.role,
              style: const TextStyle(
                color: Colors.white,
                fontSize: 12,
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
        ),
        Row(
          children: [
            Text(
              'Access granted at: ${formatShortTimestamp(user.accessGrantedAt)}',
              style: const TextStyle(fontSize: 12),
            ),

            if (device.isOwner && !user.isOwner) ...[
              const SizedBox(width: 8),
              IconButton(
                onPressed: () => _showRemoveUserConfirmation(user, device),
                icon: const Icon(Icons.delete, color: Colors.red),
                iconSize: 20,
              ),
            ],
          ],
        ),
      ],
    );
  }

  Widget _buildInfoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 120,
            child: Text(
              label,
              style: const TextStyle(
                fontWeight: FontWeight.w500,
                color: Colors.grey,
              ),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: const TextStyle(fontWeight: FontWeight.w500),
            ),
          ),
        ],
      ),
    );
  }

  void _showAddUserDialog(BuildContext context, Device device) {
    showDialog(
      context: context,
      builder: (context) => AddDeviceUserDialog(device: device),
    );
  }

  void _showRemoveUserConfirmation(DeviceUser user, Device device) {
    showDialogConfirmation(
      context,
      title: 'Remove User',
      message:
          'Are you sure you want to remove "${user.name}" from the device? This action cannot be undone.',
      onConfirm: () {
        context.read<DeviceBloc>().add(
          RemoveDeviceUserEvent(sbcId: device.sbcId, userId: user.userId),
        );
      },
    );
  }

  void _showEditDeviceDialog(BuildContext context, Device device) {
    final controller = TextEditingController(text: device.deviceFriendlyName);

    showDialog(
      context: context,
      builder:
          (context) => AlertDialog(
            title: const Text('Edit Device Name'),
            content: TextField(
              controller: controller,
              decoration: const InputDecoration(
                labelText: 'Device Name',
                border: OutlineInputBorder(),
              ),
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.of(context).pop(),
                child: const Text('Cancel'),
              ),
              ElevatedButton(
                onPressed: () {
                  if (controller.text.trim().isNotEmpty) {
                    context.read<DeviceBloc>().add(
                      UpdateDeviceEvent(
                        sbcId: device.sbcId,
                        deviceFriendlyName: controller.text.trim(),
                      ),
                    );
                    Navigator.of(context).pop();
                  }
                },
                child: const Text('Save'),
              ),
            ],
          ),
    );
  }
}
