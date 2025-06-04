import 'package:flutter/material.dart';
import 'package:intl/intl.dart';

import '../../domain/entities/package_delivery.dart';

class PackageDeliveryItem extends StatelessWidget {
  final PackageDelivery delivery;
  final VoidCallback? onTap;
  final VoidCallback? onEdit;
  final VoidCallback? onDelete;
  final VoidCallback? onMarkAsRetrieved;

  const PackageDeliveryItem({
    super.key,
    required this.delivery,
    this.onTap,
    this.onEdit,
    this.onDelete,
    this.onMarkAsRetrieved,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Expanded(
                    child: Text(
                      delivery.itemDescription,
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                  _buildStatusChip(context),
                ],
              ),
              const SizedBox(height: 8),
              if (delivery.trackingNumber != null) ...[
                Row(
                  children: [
                    const Icon(
                      Icons.local_shipping,
                      size: 16,
                      color: Colors.grey,
                    ),
                    const SizedBox(width: 8),
                    Text(
                      'Tracking: ${delivery.trackingNumber}',
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                  ],
                ),
                const SizedBox(height: 4),
              ],
              if (delivery.carrier != null) ...[
                Row(
                  children: [
                    const Icon(Icons.business, size: 16, color: Colors.grey),
                    const SizedBox(width: 8),
                    Text(
                      'Carrier: ${delivery.carrier}',
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                  ],
                ),
                const SizedBox(height: 4),
              ],
              Row(
                children: [
                  const Icon(
                    Icons.calendar_today,
                    size: 16,
                    color: Colors.grey,
                  ),
                  const SizedBox(width: 8),
                  Text(
                    'Expected: ${DateFormat('MMM dd, yyyy').format(delivery.expectedDate)}',
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ],
              ),
              if (delivery.receivedAtTimestamp != null) ...[
                const SizedBox(height: 4),
                Row(
                  children: [
                    const Icon(
                      Icons.check_circle,
                      size: 16,
                      color: Colors.green,
                    ),
                    const SizedBox(width: 8),
                    Text(
                      'Received: ${DateFormat('MMM dd, yyyy HH:mm').format(delivery.receivedAtTimestamp!)}',
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                  ],
                ),
              ],
              const SizedBox(height: 12),
              Row(
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  if (!delivery.isRetrieved &&
                      delivery.isReceived &&
                      onMarkAsRetrieved != null) ...[
                    TextButton.icon(
                      onPressed: onMarkAsRetrieved,
                      icon: const Icon(Icons.check),
                      label: const Text('Mark Retrieved'),
                    ),
                    const SizedBox(width: 8),
                  ],
                  if (onEdit != null) ...[
                    IconButton(
                      onPressed: onEdit,
                      icon: const Icon(Icons.edit),
                      tooltip: 'Edit',
                    ),
                  ],
                  if (onDelete != null) ...[
                    IconButton(
                      onPressed: onDelete,
                      icon: const Icon(Icons.delete),
                      tooltip: 'Delete',
                    ),
                  ],
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildStatusChip(BuildContext context) {
    Color chipColor;
    Color textColor;
    IconData icon;

    switch (delivery.status) {
      case PackageDeliveryStatus.pending:
        chipColor = Colors.orange.shade100;
        textColor = Colors.orange.shade800;
        icon = Icons.schedule;
        break;
      case PackageDeliveryStatus.inBox1:
      case PackageDeliveryStatus.inBox2:
        chipColor = Colors.blue.shade100;
        textColor = Colors.blue.shade800;
        icon = Icons.inbox;
        break;
      case PackageDeliveryStatus.retrievedByUser:
        chipColor = Colors.green.shade100;
        textColor = Colors.green.shade800;
        icon = Icons.check_circle;
        break;
      case PackageDeliveryStatus.cancelled:
        chipColor = Colors.red.shade100;
        textColor = Colors.red.shade800;
        icon = Icons.cancel;
        break;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      decoration: BoxDecoration(
        color: chipColor,
        borderRadius: BorderRadius.circular(16),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 16, color: textColor),
          const SizedBox(width: 4),
          Text(
            delivery.status.displayName,
            style: TextStyle(
              color: textColor,
              fontSize: 12,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }
}
