import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../domain/entities/visitor_permission.dart';
import '../blocs/visitor_permission_bloc.dart';

class EditVisitorPermissionDialog extends StatefulWidget {
  final VisitorPermission permission;

  const EditVisitorPermissionDialog({super.key, required this.permission});

  @override
  State<EditVisitorPermissionDialog> createState() =>
      _EditVisitorPermissionDialogState();
}

class _EditVisitorPermissionDialogState
    extends State<EditVisitorPermissionDialog> {
  late final TextEditingController _nameController;
  late PermissionLevel _selectedPermissionLevel;
  final _formKey = GlobalKey<FormState>();

  @override
  void initState() {
    super.initState();
    _nameController = TextEditingController(
      text: widget.permission.visitorName,
    );
    _selectedPermissionLevel = widget.permission.permissionLevel;
  }

  @override
  void dispose() {
    _nameController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Edit Visitor Permission'),
      content: Form(
        key: _formKey,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            TextFormField(
              controller: _nameController,
              decoration: const InputDecoration(
                labelText: 'Visitor Name',
                border: OutlineInputBorder(),
                prefixIcon: Icon(Icons.person),
              ),
              validator: (value) {
                if (value == null || value.trim().isEmpty) {
                  return 'Visitor name is required';
                }
                if (value.trim().length < 2) {
                  return 'Visitor name must be at least 2 characters';
                }
                return null;
              },
            ),
            const SizedBox(height: 16),
            const Text(
              'Permission Level',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.w500),
            ),
            const SizedBox(height: 8),
            Column(
              children:
                  PermissionLevel.values.map((level) {
                    return RadioListTile<PermissionLevel>(
                      title: Row(
                        children: [
                          Icon(
                            _getPermissionIcon(level),
                            color: _getPermissionColor(level),
                            size: 20,
                          ),
                          const SizedBox(width: 8),
                          Text(level.value),
                        ],
                      ),
                      subtitle: Text(_getPermissionDescription(level)),
                      value: level,
                      groupValue: _selectedPermissionLevel,
                      onChanged: (value) {
                        if (value != null) {
                          setState(() {
                            _selectedPermissionLevel = value;
                          });
                        }
                      },
                    );
                  }).toList(),
            ),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('Cancel'),
        ),
        ElevatedButton(onPressed: _saveChanges, child: const Text('Save')),
      ],
    );
  }

  void _saveChanges() {
    if (!_formKey.currentState!.validate()) {
      return;
    }

    final trimmedName = _nameController.text.trim();

    // Check if there are any changes
    if (trimmedName == widget.permission.visitorName &&
        _selectedPermissionLevel == widget.permission.permissionLevel) {
      Navigator.of(context).pop();
      return;
    }

    context.read<VisitorPermissionBloc>().add(
      UpdateVisitorPermissionEvent(
        faceTagId: widget.permission.faceTagId,
        visitorName: trimmedName,
        permissionLevel: _selectedPermissionLevel,
      ),
    );

    Navigator.of(context).pop();
  }

  Color _getPermissionColor(PermissionLevel level) {
    switch (level) {
      case PermissionLevel.allowed:
        return Colors.green;
      case PermissionLevel.denied:
        return Colors.red;
    }
  }

  IconData _getPermissionIcon(PermissionLevel level) {
    switch (level) {
      case PermissionLevel.allowed:
        return Icons.check_circle;
      case PermissionLevel.denied:
        return Icons.block;
    }
  }

  String _getPermissionDescription(PermissionLevel level) {
    switch (level) {
      case PermissionLevel.allowed:
        return 'Can leave video messages';
      case PermissionLevel.denied:
        return 'Access denied - no permissions granted';
    }
  }
}
