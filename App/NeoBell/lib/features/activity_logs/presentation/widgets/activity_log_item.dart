import 'package:flutter/material.dart';
import 'package:neobell/core/utils/date_formatter_utils.dart';
import '../../domain/entities/activity_log.dart';

class ActivityLogItem extends StatelessWidget {
  final ActivityLog activityLog;
  final VoidCallback? onTap;

  const ActivityLogItem({super.key, required this.activityLog, this.onTap});

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: ListTile(
        leading: _buildEventIcon(),
        title: Text(
          activityLog.summary,
          style: const TextStyle(fontWeight: FontWeight.w500, fontSize: 14),
        ),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const SizedBox(height: 4),
            Text(
              _formatEventType(activityLog.eventType),
              style: TextStyle(
                color: _getEventTypeColor(),
                fontWeight: FontWeight.w500,
                fontSize: 12,
              ),
            ),
            const SizedBox(height: 2),
            Text(
              formatRelativeTime(activityLog.timestamp),
              style: const TextStyle(color: Colors.grey, fontSize: 12),
            ),
            if (activityLog.sbcIdRelated != null) ...[
              const SizedBox(height: 2),
              Text(
                'Device: ${activityLog.sbcIdRelated}',
                style: const TextStyle(color: Colors.grey, fontSize: 11),
              ),
            ],
          ],
        ),
        trailing: const Icon(Icons.chevron_right, color: Colors.grey),
        onTap: onTap,
      ),
    );
  }

  Widget _buildEventIcon() {
    IconData iconData;
    Color color;

    switch (activityLog.eventType) {
      case 'doorbell_pressed':
        iconData = Icons.doorbell;
        color = Colors.blue;
        break;
      case 'video_message_recorded':
        iconData = Icons.video_camera_back;
        color = Colors.green;
        break;
      case 'package_detected':
        iconData = Icons.local_shipping;
        color = Colors.orange;
        break;
      case 'visitor_detected':
        iconData = Icons.person;
        color = Colors.purple;
        break;
      case 'device_status_change':
        iconData = Icons.settings;
        color = Colors.grey;
        break;
      case 'user_access_granted':
      case 'user_access_removed':
        iconData = Icons.security;
        color = Colors.red;
        break;
      case 'settings_changed':
      case 'permission_updated':
        iconData = Icons.tune;
        color = Colors.indigo;
        break;
      case 'firmware_update':
      case 'device_registered':
      case 'device_removed':
        iconData = Icons.memory;
        color = Colors.teal;
        break;
      case 'error_occurred':
        iconData = Icons.error;
        color = Colors.red;
        break;
      default:
        iconData = Icons.info;
        color = Colors.grey;
    }

    return CircleAvatar(
      radius: 20,
      backgroundColor: color.withOpacity(0.1),
      child: Icon(iconData, color: color, size: 20),
    );
  }

  Color _getEventTypeColor() {
    switch (activityLog.eventType) {
      case 'doorbell_pressed':
        return Colors.blue;
      case 'video_message_recorded':
        return Colors.green;
      case 'package_detected':
        return Colors.orange;
      case 'visitor_detected':
        return Colors.purple;
      case 'error_occurred':
        return Colors.red;
      default:
        return Colors.grey;
    }
  }

  String _formatEventType(String eventType) {
    return eventType
        .split('_')
        .map((word) => word[0].toUpperCase() + word.substring(1))
        .join(' ');
  }
}
