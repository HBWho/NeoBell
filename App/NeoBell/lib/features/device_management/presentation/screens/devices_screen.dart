import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/common/widgets/base_screen_widget.dart';
import '../../../../core/utils/show_snackbar.dart';
import '../../domain/entities/device.dart';
import '../blocs/device_bloc.dart';
import '../widgets/device_item.dart';
import '../widgets/add_device_user_dialog.dart';

class DevicesScreen extends StatefulWidget {
  const DevicesScreen({super.key});

  @override
  State<DevicesScreen> createState() => _DevicesScreenState();
}

class _DevicesScreenState extends State<DevicesScreen> {
  @override
  void initState() {
    super.initState();
    _initializeDevices();
  }

  void _initializeDevices() {
    final currentState = context.read<DeviceBloc>().state;
    if (currentState is DeviceInitial) {
      context.read<DeviceBloc>().add(const LoadDevices());
    }
  }

  @override
  Widget build(BuildContext context) {
    return BaseScreenWidget(
      title: 'My NeoBell Devices',
      actions: [
        IconButton(
          icon: const Icon(Icons.refresh),
          onPressed: () {
            context.read<DeviceBloc>().add(RefreshDevices());
          },
        ),
      ],
      body: BlocConsumer<DeviceBloc, DeviceState>(
        listener: (context, state) {
          if (state is DeviceFailure) {
            showSnackBar(context, message: state.message, isError: true);
          } else if (state is DeviceOperationSuccess) {
            showSnackBar(context, message: state.message, isSucess: true);
          }
        },
        builder: (context, state) {
          if (state is DeviceLoading && state.devices.isEmpty) {
            return const Center(child: CircularProgressIndicator());
          } else if (state is DeviceFailure && state.devices.isEmpty) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.error_outline, size: 64, color: Colors.red),
                  const SizedBox(height: 16),
                  Text(
                    'Error loading devices',
                    style: TextStyle(fontSize: 18, color: Colors.red[700]),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    state.message,
                    textAlign: TextAlign.center,
                    style: const TextStyle(color: Colors.grey),
                  ),
                  const SizedBox(height: 16),
                  ElevatedButton(
                    onPressed: () {
                      context.read<DeviceBloc>().add(RefreshDevices());
                    },
                    child: const Text('Try Again'),
                  ),
                ],
              ),
            );
          }

          if (state.devices.isEmpty) {
            return const Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.devices_other, size: 64, color: Colors.grey),
                  SizedBox(height: 16),
                  Text(
                    'No Devices Found',
                    style: TextStyle(fontSize: 18, color: Colors.grey),
                  ),
                  SizedBox(height: 8),
                  Text(
                    'Your NeoBell devices will appear here when they are linked to your account',
                    textAlign: TextAlign.center,
                    style: TextStyle(color: Colors.grey),
                  ),
                ],
              ),
            );
          }

          return RefreshIndicator(
            onRefresh: () async {
              context.read<DeviceBloc>().add(RefreshDevices());
            },
            child: ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: state.devices.length,
              itemBuilder: (context, index) {
                final device = state.devices[index];
                return DeviceItem(
                  device: device,
                  onTap:
                      () => context.pushNamed(
                        'device-details',
                        pathParameters: {'sbcId': device.sbcId},
                      ),
                  onAddUser:
                      device.isOwner
                          ? () => _showAddUserDialog(context, device)
                          : null,
                  onEdit:
                      device.isOwner
                          ? () => _showEditDeviceDialog(context, device)
                          : null,
                );
              },
            ),
          );
        },
      ),
    );
  }

  void _showAddUserDialog(BuildContext context, Device device) {
    showDialog(
      context: context,
      builder: (context) => AddDeviceUserDialog(device: device),
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
