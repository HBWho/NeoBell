import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../../../core/utils/email_checker_utils.dart' as email_utils;
import '../../domain/entities/device.dart';
import '../blocs/device_bloc.dart';

class AddDeviceUserDialog extends StatefulWidget {
  final Device device;

  const AddDeviceUserDialog({super.key, required this.device});

  @override
  State<AddDeviceUserDialog> createState() => _AddDeviceUserDialogState();
}

class _AddDeviceUserDialogState extends State<AddDeviceUserDialog> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  bool _isLoading = false;

  @override
  void dispose() {
    _emailController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return BlocListener<DeviceBloc, DeviceState>(
      listener: (context, state) {
        if (state is DeviceOperationSuccess) {
          setState(() => _isLoading = false);
          Navigator.of(context).pop();
        } else if (state is DeviceFailure) {
          setState(() => _isLoading = false);
        } else if (state is DeviceLoading) {
          setState(() => _isLoading = true);
        }
      },
      child: AlertDialog(
        title: const Text('Adicionar Usuário'),
        content: Form(
          key: _formKey,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Add a new user to "${widget.device.deviceFriendlyName}"',
                style: const TextStyle(fontSize: 14),
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _emailController,
                keyboardType: TextInputType.emailAddress,
                decoration: const InputDecoration(
                  labelText: 'User Email',
                  hintText: 'user@example.com',
                  border: OutlineInputBorder(),
                  prefixIcon: Icon(Icons.email),
                ),
                validator: (value) {
                  if (value == null || value.trim().isEmpty) {
                    return 'Please enter an email';
                  }
                  if (!email_utils.isValidEmail(value.trim())) {
                    return 'Please enter a valid email';
                  }
                  return null;
                },
                enabled: !_isLoading,
              ),
              const SizedBox(height: 8),
              Text(
                'The user will be added as a "Resident" and will have access to the device.',
                style: TextStyle(fontSize: 12, color: Colors.grey[600]),
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: _isLoading ? null : () => Navigator.of(context).pop(),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: _isLoading ? null : _addUser,
            child:
                _isLoading
                    ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                    : const Text('Adicionar'),
          ),
        ],
      ),
    );
  }

  void _addUser() {
    if (_formKey.currentState!.validate()) {
      context.read<DeviceBloc>().add(
        AddDeviceUserEvent(
          sbcId: widget.device.sbcId,
          userEmail: _emailController.text.trim(),
        ),
      );
    }
  }
}
