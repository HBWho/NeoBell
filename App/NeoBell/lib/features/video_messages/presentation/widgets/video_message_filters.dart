import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:neobell/core/utils/date_formatter_utils.dart';
import '../blocs/video_message_bloc.dart';
import '../blocs/video_message_event.dart';

class VideoMessageFilters extends StatefulWidget {
  const VideoMessageFilters({super.key});

  @override
  State<VideoMessageFilters> createState() => _VideoMessageFiltersState();
}

class _VideoMessageFiltersState extends State<VideoMessageFilters> {
  String? selectedDevice;
  DateTime? startDate;
  DateTime? endDate;
  bool? isViewed;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const Text(
            'Filter Messages',
            style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 16),
          DropdownButtonFormField<String>(
            value: selectedDevice,
            decoration: const InputDecoration(
              labelText: 'Device',
              border: OutlineInputBorder(),
            ),
            items: const [
              DropdownMenuItem(value: null, child: Text('All Devices')),
              // TODO: Add devices from state
            ],
            onChanged: (value) {
              setState(() {
                selectedDevice = value;
              });
            },
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              Expanded(
                child: TextButton.icon(
                  onPressed: () => _selectDate(context, true),
                  icon: const Icon(Icons.calendar_today),
                  label: Text(
                    startDate != null
                        ? formatDateOnly(startDate!)
                        : 'Start Date',
                  ),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: TextButton.icon(
                  onPressed: () => _selectDate(context, false),
                  icon: const Icon(Icons.calendar_today),
                  label: Text(
                    endDate != null ? formatDateOnly(endDate!) : 'End Date',
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),
          DropdownButtonFormField<bool?>(
            value: isViewed,
            decoration: const InputDecoration(
              labelText: 'View Status',
              border: OutlineInputBorder(),
            ),
            items: const [
              DropdownMenuItem(value: null, child: Text('All Messages')),
              DropdownMenuItem(value: true, child: Text('Viewed')),
              DropdownMenuItem(value: false, child: Text('Not Viewed')),
            ],
            onChanged: (value) {
              setState(() {
                isViewed = value;
              });
            },
          ),
          const SizedBox(height: 24),
          Row(
            mainAxisAlignment: MainAxisAlignment.end,
            children: [
              TextButton(onPressed: _clearFilters, child: const Text('Clear')),
              const SizedBox(width: 16),
              ElevatedButton(
                onPressed: _applyFilters,
                child: const Text('Apply'),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Future<void> _selectDate(BuildContext context, bool isStart) async {
    final DateTime? picked = await showDatePicker(
      context: context,
      initialDate: DateTime.now(),
      firstDate: DateTime(2020),
      lastDate: DateTime.now(),
    );

    if (picked != null) {
      setState(() {
        if (isStart) {
          startDate = picked;
        } else {
          endDate = picked;
        }
      });
    }
  }

  void _clearFilters() {
    setState(() {
      selectedDevice = null;
      startDate = null;
      endDate = null;
      isViewed = null;
    });
    _applyFilters();
  }

  void _applyFilters() {
    context.read<VideoMessageBloc>().add(
      GetVideoMessagesEvent(
        sbcId: selectedDevice,
        startDate: startDate,
        endDate: endDate,
        isViewed: isViewed,
      ),
    );
    Navigator.pop(context);
  }
}
