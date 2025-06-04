import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../../domain/entities/visitor_permission.dart';

class VisitorPermissionItem extends StatelessWidget {
  final VisitorPermission permission;
  final VoidCallback? onTap;
  final VoidCallback onEdit;
  final VoidCallback onDelete;

  const VisitorPermissionItem({
    super.key,
    required this.permission,
    this.onTap,
    required this.onEdit,
    required this.onDelete,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final dateFormat = DateFormat('MMM dd, yyyy HH:mm');

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
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
                  CircleAvatar(
                    backgroundColor: _getPermissionColor(
                      permission.permissionLevel,
                    ),
                    child: Icon(
                      _getPermissionIcon(permission.permissionLevel),
                      color: Colors.white,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          permission.visitorName,
                          style: theme.textTheme.titleMedium?.copyWith(
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 4),
                        Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 8,
                            vertical: 4,
                          ),
                          decoration: BoxDecoration(
                            color: _getPermissionColor(
                              permission.permissionLevel,
                            ).withOpacity(0.1),
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(
                              color: _getPermissionColor(
                                permission.permissionLevel,
                              ).withOpacity(0.3),
                            ),
                          ),
                          child: Text(
                            permission.permissionLevel.value,
                            style: theme.textTheme.labelSmall?.copyWith(
                              color: _getPermissionColor(
                                permission.permissionLevel,
                              ),
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  PopupMenuButton<String>(
                    onSelected: (value) {
                      switch (value) {
                        case 'edit':
                          onEdit();
                          break;
                        case 'delete':
                          onDelete();
                          break;
                      }
                    },
                    itemBuilder:
                        (context) => [
                          const PopupMenuItem(
                            value: 'edit',
                            child: Row(
                              children: [
                                Icon(Icons.edit, size: 20),
                                SizedBox(width: 8),
                                Text('Edit'),
                              ],
                            ),
                          ),
                          const PopupMenuItem(
                            value: 'delete',
                            child: Row(
                              children: [
                                Icon(Icons.delete, size: 20, color: Colors.red),
                                SizedBox(width: 8),
                                Text(
                                  'Delete',
                                  style: TextStyle(color: Colors.red),
                                ),
                              ],
                            ),
                          ),
                        ],
                  ),
                ],
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  Icon(Icons.access_time, size: 16, color: Colors.grey[600]),
                  const SizedBox(width: 4),
                  Text(
                    'Created: ${dateFormat.format(permission.createdAt)}',
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: Colors.grey[600],
                    ),
                  ),
                ],
              ),
              if (permission.lastUpdatedAt != permission.createdAt) ...[
                const SizedBox(height: 4),
                Row(
                  children: [
                    Icon(Icons.update, size: 16, color: Colors.grey[600]),
                    const SizedBox(width: 4),
                    Text(
                      'Updated: ${dateFormat.format(permission.lastUpdatedAt)}',
                      style: theme.textTheme.bodySmall?.copyWith(
                        color: Colors.grey[600],
                      ),
                    ),
                  ],
                ),
              ],
              const SizedBox(height: 8),
              Row(
                children: [
                  Icon(Icons.fingerprint, size: 16, color: Colors.grey[600]),
                  const SizedBox(width: 4),
                  Text(
                    'Face ID: ${permission.faceTagId.substring(0, 8)}...',
                    style: theme.textTheme.bodySmall?.copyWith(
                      color: Colors.grey[600],
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
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
}
