import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:neobell/core/utils/date_formatter_utils.dart';

import '../../domain/entities/create_package_delivery.dart';
import '../../domain/entities/package_delivery.dart';
import '../../domain/entities/update_package_delivery.dart';
import '../blocs/package_delivery_bloc.dart';
import '../blocs/package_delivery_event.dart';

class AddPackageDeliveryDialog extends StatefulWidget {
  final PackageDelivery? delivery;

  const AddPackageDeliveryDialog({super.key, this.delivery});

  @override
  State<AddPackageDeliveryDialog> createState() =>
      _AddPackageDeliveryDialogState();
}

class _AddPackageDeliveryDialogState extends State<AddPackageDeliveryDialog> {
  final _formKey = GlobalKey<FormState>();
  final _orderIdController = TextEditingController();
  final _itemDescriptionController = TextEditingController();
  final _trackingNumberController = TextEditingController();
  final _carrierController = TextEditingController();
  DateTime _expectedDate = DateTime.now().add(const Duration(days: 1));
  PackageDeliveryStatus? _status;

  bool get _isEditing => widget.delivery != null;

  @override
  void initState() {
    super.initState();
    if (_isEditing) {
      _orderIdController.text = widget.delivery!.orderId;
      _itemDescriptionController.text = widget.delivery!.itemDescription;
      _trackingNumberController.text = widget.delivery!.trackingNumber ?? '';
      _carrierController.text = widget.delivery!.carrier ?? '';
      _expectedDate = widget.delivery!.expectedDate;
      _status = widget.delivery!.status;
    }
  }

  @override
  void dispose() {
    _orderIdController.dispose();
    _itemDescriptionController.dispose();
    _trackingNumberController.dispose();
    _carrierController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Text(_isEditing ? 'Edit Delivery' : 'Add Package Delivery'),
      content: ConstrainedBox(
        constraints: const BoxConstraints(minWidth: 300, maxWidth: 600),
        child: Form(
          key: _formKey,
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                TextFormField(
                  controller: _orderIdController,
                  readOnly: _isEditing,
                  decoration: const InputDecoration(
                    labelText: 'Order ID *',
                    hintText: 'e.g., 123456',
                    border: OutlineInputBorder(),
                  ),
                  validator: (value) {
                    if (value == null || value.trim().isEmpty) {
                      return 'Please enter order ID';
                    }
                    return null;
                  },
                ),
                const SizedBox(height: 16),
                TextFormField(
                  controller: _itemDescriptionController,
                  decoration: const InputDecoration(
                    labelText: 'Item Description *',
                    hintText: 'e.g., New Headphones',
                    border: OutlineInputBorder(),
                  ),
                  validator: (value) {
                    if (value == null || value.trim().isEmpty) {
                      return 'Please enter item description';
                    }
                    return null;
                  },
                  maxLines: 2,
                ),
                const SizedBox(height: 16),
                TextFormField(
                  controller: _trackingNumberController,
                  decoration: const InputDecoration(
                    labelText: 'Tracking Number',
                    hintText: 'e.g., 1Z999AA10123456784',
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 16),
                TextFormField(
                  controller: _carrierController,
                  decoration: const InputDecoration(
                    labelText: 'Carrier',
                    hintText: 'e.g., UPS, FedEx, DHL',
                    border: OutlineInputBorder(),
                  ),
                ),
                const SizedBox(height: 16),
                InkWell(
                  onTap: _selectExpectedDate,
                  child: InputDecorator(
                    decoration: const InputDecoration(
                      labelText: 'Expected Date *',
                      border: OutlineInputBorder(),
                      suffixIcon: Icon(Icons.calendar_today),
                    ),
                    child: Text(formatDateOnly(_expectedDate)),
                  ),
                ),
                const SizedBox(height: 16),
                if (_isEditing)
                  DropdownButtonFormField<PackageDeliveryStatus>(
                    value: widget.delivery!.status,
                    decoration: const InputDecoration(
                      labelText: 'Status',
                      border: OutlineInputBorder(),
                    ),
                    items:
                        PackageDeliveryStatus.values.map((status) {
                          return DropdownMenuItem(
                            value: status,
                            child: Text(status.displayName),
                          );
                        }).toList(),
                    onChanged: (value) {
                      if (value != null) {
                        setState(() {
                          _status = value;
                        });
                      }
                    },
                  ),
              ],
            ),
          ),
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('Cancel'),
        ),
        ElevatedButton(
          onPressed: _saveDelivery,
          child: Text(_isEditing ? 'Update' : 'Add'),
        ),
      ],
    );
  }

  Future<void> _selectExpectedDate() async {
    final selectedDate = await showDatePicker(
      context: context,
      initialDate: _expectedDate,
      firstDate: DateTime.now(),
      lastDate: DateTime.now().add(const Duration(days: 365)),
    );

    if (selectedDate != null) {
      setState(() {
        _expectedDate = selectedDate;
      });
    }
  }

  void _saveDelivery() {
    if (!_formKey.currentState!.validate()) {
      return;
    }

    if (_isEditing) {
      _updateDelivery();
    } else {
      _createDelivery();
    }
  }

  void _createDelivery() {
    final delivery = CreatePackageDelivery(
      orderId: _orderIdController.text.trim(),
      itemDescription: _itemDescriptionController.text.trim(),
      trackingNumber:
          _trackingNumberController.text.trim().isEmpty
              ? null
              : _trackingNumberController.text.trim(),
      carrier:
          _carrierController.text.trim().isEmpty
              ? null
              : _carrierController.text.trim(),
      expectedDate: _expectedDate,
    );

    context.read<PackageDeliveryBloc>().add(
      CreatePackageDeliveryEvent(delivery),
    );

    Navigator.of(context).pop();
  }

  void _updateDelivery() {
    final delivery = UpdatePackageDelivery(
      itemDescription: _itemDescriptionController.text.trim(),
      trackingNumber:
          _trackingNumberController.text.trim().isEmpty
              ? null
              : _trackingNumberController.text.trim(),
      carrier:
          _carrierController.text.trim().isEmpty
              ? null
              : _carrierController.text.trim(),
      expectedDate: _expectedDate,
      status: _status,
    );

    context.read<PackageDeliveryBloc>().add(
      UpdatePackageDeliveryEvent(
        orderId: widget.delivery!.orderId,
        delivery: delivery,
      ),
    );

    Navigator.of(context).pop();
  }
}
