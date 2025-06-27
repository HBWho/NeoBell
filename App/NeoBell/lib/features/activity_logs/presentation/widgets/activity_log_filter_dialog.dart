import 'package:flutter/material.dart';
import 'package:neobell/core/utils/date_formatter_utils.dart';
import '../../domain/entities/activity_log_filter.dart';

class ActivityLogFilterDialog extends StatefulWidget {
  final ActivityLogFilter currentFilter;
  final Function(ActivityLogFilter) onApplyFilter;

  const ActivityLogFilterDialog({
    super.key,
    required this.currentFilter,
    required this.onApplyFilter,
  });

  @override
  State<ActivityLogFilterDialog> createState() =>
      _ActivityLogFilterDialogState();
}

class _ActivityLogFilterDialogState extends State<ActivityLogFilterDialog> {
  late List<String> _selectedEventTypes;
  String? _selectedDeviceId;
  DateTime? _startDate;
  DateTime? _endDate;
  int _limit = 20;

  // Available event types based on the API documentation
  final List<String> _availableEventTypes = [
    'doorbell_pressed',
    'video_message_recorded',
    'package_detected',
    'visitor_detected',
    'device_status_change',
    'user_access_granted',
    'user_access_removed',
    'settings_changed',
    'permission_updated',
    'firmware_update',
    'device_registered',
    'device_removed',
    'error_occurred',
  ];

  @override
  void initState() {
    super.initState();
    _selectedEventTypes = widget.currentFilter.eventTypes ?? [];
    _selectedDeviceId = widget.currentFilter.sbcId;
    _startDate = widget.currentFilter.startDate;
    _endDate = widget.currentFilter.endDate;
    _limit = widget.currentFilter.limit ?? 20;
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Filter Activity Logs'),
      content: SizedBox(
        width: double.maxFinite,
        child: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              _buildEventTypesSection(),
              const SizedBox(height: 16),
              _buildDeviceSection(),
              const SizedBox(height: 16),
              _buildDateRangeSection(),
              const SizedBox(height: 16),
              _buildLimitSection(),
            ],
          ),
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('Cancel'),
        ),
        TextButton(onPressed: _clearFilters, child: const Text('Clear')),
        ElevatedButton(onPressed: _applyFilters, child: const Text('Apply')),
      ],
    );
  }

  Widget _buildEventTypesSection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Event Types',
          style: TextStyle(fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 8),
        SizedBox(
          height: 200,
          child: ListView.builder(
            itemCount: _availableEventTypes.length,
            itemBuilder: (context, index) {
              final eventType = _availableEventTypes[index];
              return CheckboxListTile(
                title: Text(_formatEventType(eventType)),
                value: _selectedEventTypes.contains(eventType),
                onChanged: (bool? value) {
                  setState(() {
                    if (value == true) {
                      _selectedEventTypes.add(eventType);
                    } else {
                      _selectedEventTypes.remove(eventType);
                    }
                  });
                },
                dense: true,
              );
            },
          ),
        ),
      ],
    );
  }

  Widget _buildDeviceSection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('Device ID', style: TextStyle(fontWeight: FontWeight.bold)),
        const SizedBox(height: 8),
        TextFormField(
          initialValue: _selectedDeviceId,
          decoration: const InputDecoration(
            hintText: 'Enter device ID (optional)',
            border: OutlineInputBorder(),
          ),
          onChanged: (value) {
            _selectedDeviceId = value.isEmpty ? null : value;
          },
        ),
      ],
    );
  }

  Widget _buildDateRangeSection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('Date Range', style: TextStyle(fontWeight: FontWeight.bold)),
        const SizedBox(height: 8),
        Row(
          children: [
            Expanded(
              child: OutlinedButton(
                onPressed: () => _selectDate(context, true),
                child: Text(
                  _startDate != null
                      ? formatDateOnly(_startDate!)
                      : 'Start Date',
                ),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: OutlinedButton(
                onPressed: () => _selectDate(context, false),
                child: Text(
                  _endDate != null ? formatDateOnly(_endDate!) : 'End Date',
                ),
              ),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildLimitSection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Results Limit',
          style: TextStyle(fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 8),
        DropdownButtonFormField<int>(
          value: _limit,
          decoration: const InputDecoration(border: OutlineInputBorder()),
          items:
              [10, 20, 50, 100].map((int value) {
                return DropdownMenuItem<int>(
                  value: value,
                  child: Text('$value items'),
                );
              }).toList(),
          onChanged: (int? newValue) {
            if (newValue != null) {
              setState(() {
                _limit = newValue;
              });
            }
          },
        ),
      ],
    );
  }

  Future<void> _selectDate(BuildContext context, bool isStartDate) async {
    final DateTime? picked = await showDatePicker(
      context: context,
      initialDate:
          isStartDate
              ? (_startDate ?? DateTime.now())
              : (_endDate ?? DateTime.now()),
      firstDate: DateTime(2020),
      lastDate: DateTime.now().add(const Duration(days: 1)),
    );

    if (picked != null) {
      setState(() {
        if (isStartDate) {
          _startDate = picked;
        } else {
          _endDate = picked;
        }
      });
    }
  }

  String _formatEventType(String eventType) {
    return eventType
        .split('_')
        .map((word) => word[0].toUpperCase() + word.substring(1))
        .join(' ');
  }

  void _clearFilters() {
    setState(() {
      _selectedEventTypes.clear();
      _selectedDeviceId = null;
      _startDate = null;
      _endDate = null;
      _limit = 20;
    });
  }

  void _applyFilters() {
    final filter = ActivityLogFilter(
      eventTypes: _selectedEventTypes.isEmpty ? null : _selectedEventTypes,
      sbcId: _selectedDeviceId,
      startDate: _startDate,
      endDate: _endDate,
      limit: _limit,
    );

    widget.onApplyFilter(filter);
    Navigator.of(context).pop();
  }
}
