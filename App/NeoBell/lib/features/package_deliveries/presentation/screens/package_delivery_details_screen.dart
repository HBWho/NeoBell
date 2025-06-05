import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:intl/intl.dart';

import '../../../../core/utils/show_snackbar.dart';
import '../../domain/entities/package_delivery.dart';
import '../../domain/entities/update_package_delivery.dart';
import '../blocs/package_delivery_bloc.dart';
import '../blocs/package_delivery_event.dart';
import '../blocs/package_delivery_state.dart';
import '../widgets/add_package_delivery_dialog.dart';

class PackageDeliveryDetailsScreen extends StatefulWidget {
  final String orderId;

  const PackageDeliveryDetailsScreen({super.key, required this.orderId});

  @override
  State<PackageDeliveryDetailsScreen> createState() =>
      _PackageDeliveryDetailsScreenState();
}

class _PackageDeliveryDetailsScreenState
    extends State<PackageDeliveryDetailsScreen> {
  @override
  void initState() {
    super.initState();
    context.read<PackageDeliveryBloc>().add(
      LoadPackageDeliveryDetails(widget.orderId),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Delivery Details'),
        actions: [
          BlocBuilder<PackageDeliveryBloc, PackageDeliveryState>(
            builder: (context, state) {
              if (state is PackageDeliveryDetailsLoaded) {
                return PopupMenuButton<String>(
                  onSelected:
                      (value) => _handleMenuAction(value, state.delivery),
                  itemBuilder:
                      (context) => [
                        const PopupMenuItem(
                          value: 'edit',
                          child: ListTile(
                            leading: Icon(Icons.edit),
                            title: Text('Edit'),
                            contentPadding: EdgeInsets.zero,
                          ),
                        ),
                        if (!state.delivery.isRetrieved &&
                            state.delivery.isReceived)
                          const PopupMenuItem(
                            value: 'mark_retrieved',
                            child: ListTile(
                              leading: Icon(Icons.check),
                              title: Text('Mark as Retrieved'),
                              contentPadding: EdgeInsets.zero,
                            ),
                          ),
                        const PopupMenuItem(
                          value: 'delete',
                          child: ListTile(
                            leading: Icon(Icons.delete, color: Colors.red),
                            title: Text(
                              'Delete',
                              style: TextStyle(color: Colors.red),
                            ),
                            contentPadding: EdgeInsets.zero,
                          ),
                        ),
                      ],
                );
              }
              return const SizedBox.shrink();
            },
          ),
        ],
      ),
      body: BlocConsumer<PackageDeliveryBloc, PackageDeliveryState>(
        listener: (context, state) {
          if (state is PackageDeliveryError) {
            showSnackBar(context, message: state.message, isError: true);
          } else if (state is PackageDeliveryOperationSuccess) {
            showSnackBar(context, message: state.message, isSucess: true);
            if (state.message.contains('deleted')) {
              Navigator.of(context).pop();
            } else {
              // Reload details after update
              context.read<PackageDeliveryBloc>().add(
                LoadPackageDeliveryDetails(widget.orderId),
              );
            }
          }
        },
        builder: (context, state) {
          if (state is PackageDeliveryDetailsLoading) {
            return const Center(child: CircularProgressIndicator());
          }

          if (state is PackageDeliveryError) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.error_outline, size: 64, color: Colors.grey[400]),
                  const SizedBox(height: 16),
                  Text(
                    'Error loading delivery details',
                    style: Theme.of(context).textTheme.headlineSmall,
                  ),
                  const SizedBox(height: 8),
                  Text(
                    state.message,
                    textAlign: TextAlign.center,
                    style: Theme.of(context).textTheme.bodyMedium,
                  ),
                  const SizedBox(height: 16),
                  ElevatedButton(
                    onPressed: () {
                      context.read<PackageDeliveryBloc>().add(
                        LoadPackageDeliveryDetails(widget.orderId),
                      );
                    },
                    child: const Text('Retry'),
                  ),
                ],
              ),
            );
          }

          if (state is PackageDeliveryDetailsLoaded) {
            return _buildDeliveryDetails(context, state.delivery);
          }

          return const SizedBox.shrink();
        },
      ),
    );
  }

  Widget _buildDeliveryDetails(BuildContext context, PackageDelivery delivery) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildStatusCard(context, delivery),
          const SizedBox(height: 16),
          _buildDetailsCard(context, delivery),
          const SizedBox(height: 16),
          _buildDatesCard(context, delivery),
          if (!delivery.isRetrieved && delivery.isReceived) ...[
            const SizedBox(height: 24),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: () => _markAsRetrieved(delivery),
                icon: const Icon(Icons.check),
                label: const Text('Mark as Retrieved'),
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.all(16),
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildStatusCard(BuildContext context, PackageDelivery delivery) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(
                  _getStatusIcon(delivery.status),
                  color: _getStatusColor(delivery.status),
                  size: 32,
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        delivery.status.displayName,
                        style: Theme.of(
                          context,
                        ).textTheme.headlineSmall?.copyWith(
                          color: _getStatusColor(delivery.status),
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      Text(
                        _getStatusDescription(delivery.status),
                        style: Theme.of(context).textTheme.bodyMedium,
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildDetailsCard(BuildContext context, PackageDelivery delivery) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Package Details',
              style: Theme.of(
                context,
              ).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 16),
            _buildDetailRow(
              context,
              'Item Description',
              delivery.itemDescription,
            ),
            if (delivery.trackingNumber != null)
              _buildDetailRow(
                context,
                'Tracking Number',
                delivery.trackingNumber!,
              ),
            if (delivery.carrier != null)
              _buildDetailRow(context, 'Carrier', delivery.carrier!),
            if (delivery.sbcIdReceivedAt != null)
              _buildDetailRow(
                context,
                'Received at Device',
                delivery.sbcIdReceivedAt!,
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildDatesCard(BuildContext context, PackageDelivery delivery) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Important Dates',
              style: Theme.of(
                context,
              ).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 16),
            _buildDetailRow(
              context,
              'Expected Date',
              DateFormat('MMM dd, yyyy').format(delivery.expectedDate),
            ),
            _buildDetailRow(
              context,
              'Added Date',
              DateFormat('MMM dd, yyyy HH:mm').format(delivery.addedAt),
            ),
            if (delivery.receivedAtTimestamp != null)
              _buildDetailRow(
                context,
                'Received Date',
                DateFormat(
                  'MMM dd, yyyy HH:mm',
                ).format(delivery.receivedAtTimestamp!),
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildDetailRow(BuildContext context, String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 120,
            child: Text(
              label,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                fontWeight: FontWeight.w500,
                color: Colors.grey[600],
              ),
            ),
          ),
          Expanded(
            child: Text(value, style: Theme.of(context).textTheme.bodyMedium),
          ),
        ],
      ),
    );
  }

  IconData _getStatusIcon(PackageDeliveryStatus status) {
    switch (status) {
      case PackageDeliveryStatus.pending:
        return Icons.schedule;
      case PackageDeliveryStatus.delivered:
        return Icons.inbox;
      case PackageDeliveryStatus.retrievedByUser:
        return Icons.check_circle;
      case PackageDeliveryStatus.cancelled:
        return Icons.cancel;
    }
  }

  Color _getStatusColor(PackageDeliveryStatus status) {
    switch (status) {
      case PackageDeliveryStatus.pending:
        return Colors.orange;
      case PackageDeliveryStatus.delivered:
        return Colors.blue;
      case PackageDeliveryStatus.retrievedByUser:
        return Colors.green;
      case PackageDeliveryStatus.cancelled:
        return Colors.red;
    }
  }

  String _getStatusDescription(PackageDeliveryStatus status) {
    switch (status) {
      case PackageDeliveryStatus.pending:
        return 'Awaiting delivery';
      case PackageDeliveryStatus.delivered:
        return 'Package delivered';
      case PackageDeliveryStatus.retrievedByUser:
        return 'Package has been collected';
      case PackageDeliveryStatus.cancelled:
        return 'Delivery was cancelled';
    }
  }

  void _handleMenuAction(String action, PackageDelivery delivery) {
    switch (action) {
      case 'edit':
        _editDelivery(delivery);
        break;
      case 'mark_retrieved':
        _markAsRetrieved(delivery);
        break;
      case 'delete':
        _deleteDelivery(delivery);
        break;
    }
  }

  void _editDelivery(PackageDelivery delivery) {
    showDialog(
      context: context,
      builder: (context) => AddPackageDeliveryDialog(delivery: delivery),
    );
  }

  void _markAsRetrieved(PackageDelivery delivery) {
    showDialog(
      context: context,
      builder:
          (context) => AlertDialog(
            title: const Text('Mark as Retrieved'),
            content: Text('Mark "${delivery.itemDescription}" as retrieved?'),
            actions: [
              TextButton(
                onPressed: () => Navigator.of(context).pop(),
                child: const Text('Cancel'),
              ),
              ElevatedButton(
                onPressed: () {
                  Navigator.of(context).pop();
                  context.read<PackageDeliveryBloc>().add(
                    UpdatePackageDeliveryEvent(
                      orderId: delivery.orderId,
                      delivery: const UpdatePackageDelivery(
                        status: PackageDeliveryStatus.retrievedByUser,
                      ),
                    ),
                  );
                },
                child: const Text('Mark Retrieved'),
              ),
            ],
          ),
    );
  }

  void _deleteDelivery(PackageDelivery delivery) {
    showDialog(
      context: context,
      builder:
          (context) => AlertDialog(
            title: const Text('Delete Delivery'),
            content: Text(
              'Are you sure you want to delete "${delivery.itemDescription}"?',
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.of(context).pop(),
                child: const Text('Cancel'),
              ),
              ElevatedButton(
                onPressed: () {
                  Navigator.of(context).pop();
                  context.read<PackageDeliveryBloc>().add(
                    DeletePackageDeliveryEvent(delivery.orderId),
                  );
                },
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.red,
                  foregroundColor: Colors.white,
                ),
                child: const Text('Delete'),
              ),
            ],
          ),
    );
  }
}
