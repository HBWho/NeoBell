import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import 'package:neobell/core/utils/date_formatter_utils.dart';
import '../../../../core/common/widgets/base_screen_widget.dart';
import '../../../../core/utils/show_snackbar.dart';
import '../../domain/entities/activity_log.dart';
import '../blocs/activity_log_bloc.dart';

class ActivityLogDetailsScreen extends StatefulWidget {
  final String logSourceId;
  final String timestampUuid;

  const ActivityLogDetailsScreen({
    super.key,
    required this.logSourceId,
    required this.timestampUuid,
  });

  @override
  State<ActivityLogDetailsScreen> createState() =>
      _ActivityLogDetailsScreenState();
}

class _ActivityLogDetailsScreenState extends State<ActivityLogDetailsScreen> {
  @override
  void initState() {
    super.initState();
    context.read<ActivityLogBloc>().add(
      SelectActivityLogFromCache(
        logSourceId: widget.logSourceId,
        timestampUuid: widget.timestampUuid,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return BaseScreenWidget(
      title: 'Activity Details',
      body: BlocConsumer<ActivityLogBloc, ActivityLogState>(
        listener: (context, state) {
          if (state is ActivityLogFailure) {
            showSnackBar(context, message: state.message, isError: true);
          }
        },
        builder: (context, state) {
          if (state is ActivityLogLoading) {
            return const Center(child: CircularProgressIndicator());
          } else if (state is ActivityLogFailure) {
            return _buildErrorWidget(state.message);
          } else if (state is ActivityLogDetailsLoaded) {
            return _buildDetailsWidget(state.currentActivityLog);
          }

          return const Center(child: Text('No details available'));
        },
      ),
    );
  }

  Widget _buildErrorWidget(String message) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.error_outline, size: 64, color: Colors.red),
          const SizedBox(height: 16),
          Text(
            'Error loading activity details',
            style: TextStyle(fontSize: 18, color: Colors.red[700]),
          ),
          const SizedBox(height: 8),
          Text(
            message,
            textAlign: TextAlign.center,
            style: const TextStyle(color: Colors.grey),
          ),
          const SizedBox(height: 16),
          ElevatedButton(
            onPressed: () => context.pop,
            child: const Text('Back to Details'),
          ),
        ],
      ),
    );
  }

  Widget _buildDetailsWidget(ActivityLog activityLog) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildHeaderSection(activityLog),
          const SizedBox(height: 24),
          _buildInfoSection(activityLog),
          if (activityLog.details != null &&
              activityLog.details!.isNotEmpty) ...[
            const SizedBox(height: 24),
            _buildDetailsSection(activityLog.details!),
          ],
        ],
      ),
    );
  }

  Widget _buildHeaderSection(ActivityLog activityLog) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                _buildEventIcon(activityLog.eventType),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        _formatEventType(activityLog.eventType),
                        style: const TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        activityLog.summary,
                        style: const TextStyle(
                          fontSize: 14,
                          color: Colors.grey,
                        ),
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

  Widget _buildInfoSection(ActivityLog activityLog) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Information',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 12),
            _buildInfoRow('Log Source ID', activityLog.logSourceId),
            _buildInfoRow('Timestamp UUID', activityLog.timestampUuid),
            _buildInfoRow(
              'Event Type',
              _formatEventType(activityLog.eventType),
            ),
            _buildInfoRow(
              'Timestamp',
              formatFullTimestamp(activityLog.timestamp),
            ),
            if (activityLog.sbcIdRelated != null)
              _buildInfoRow('Device ID', activityLog.sbcIdRelated!),
            if (activityLog.userIdRelated != null)
              _buildInfoRow('User ID', activityLog.userIdRelated!),
          ],
        ),
      ),
    );
  }

  Widget _buildDetailsSection(Map<String, dynamic> details) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Additional Details',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 12),
            ...details.entries.map((entry) {
              return _buildInfoRow(
                _formatKey(entry.key),
                entry.value?.toString() ?? 'N/A',
              );
            }),
          ],
        ),
      ),
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
          Expanded(child: Text(value, style: const TextStyle(fontSize: 14))),
        ],
      ),
    );
  }

  Widget _buildEventIcon(String eventType) {
    IconData iconData;
    Color color;

    switch (eventType) {
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
      radius: 24,
      backgroundColor: color.withValues(alpha: 0.1),
      child: Icon(iconData, color: color, size: 24),
    );
  }

  String _formatEventType(String eventType) {
    return eventType
        .split('_')
        .map((word) => word[0].toUpperCase() + word.substring(1))
        .join(' ');
  }

  String _formatKey(String key) {
    return key
        .split('_')
        .map((word) => word[0].toUpperCase() + word.substring(1))
        .join(' ');
  }
}
