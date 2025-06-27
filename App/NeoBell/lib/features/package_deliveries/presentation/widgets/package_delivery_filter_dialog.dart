import 'package:flutter/material.dart';
import 'package:neobell/core/utils/date_formatter_utils.dart';

import '../../domain/entities/package_delivery.dart';
import '../../domain/entities/package_delivery_filter.dart';

class PackageDeliveryFilterDialog extends StatefulWidget {
  final PackageDeliveryFilter? currentFilter;

  const PackageDeliveryFilterDialog({super.key, this.currentFilter});

  @override
  State<PackageDeliveryFilterDialog> createState() =>
      _PackageDeliveryFilterDialogState();
}

class _PackageDeliveryFilterDialogState
    extends State<PackageDeliveryFilterDialog> {
  final _searchController = TextEditingController();
  PackageDeliveryStatus? _selectedStatus;
  DateTime? _startDate;
  DateTime? _endDate;

  @override
  void initState() {
    super.initState();
    if (widget.currentFilter != null) {
      _searchController.text = widget.currentFilter!.searchTerm ?? '';
      _selectedStatus = widget.currentFilter!.status;
      _startDate = widget.currentFilter!.startDate;
      _endDate = widget.currentFilter!.endDate;
    }
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Filter Deliveries'),
      content: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            TextField(
              controller: _searchController,
              decoration: const InputDecoration(
                labelText: 'Search',
                hintText: 'Search by item description...',
                border: OutlineInputBorder(),
                prefixIcon: Icon(Icons.search),
              ),
            ),
            const SizedBox(height: 16),
            const Text(
              'Status',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.w500),
            ),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              children: [
                FilterChip(
                  label: const Text('All'),
                  selected: _selectedStatus == null,
                  onSelected: (selected) {
                    setState(() {
                      _selectedStatus = null;
                    });
                  },
                ),
                ...PackageDeliveryStatus.values.map(
                  (status) => FilterChip(
                    label: Text(status.displayName),
                    selected: _selectedStatus == status,
                    onSelected: (selected) {
                      setState(() {
                        _selectedStatus = selected ? status : null;
                      });
                    },
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            const Text(
              'Date Range',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.w500),
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                Expanded(
                  child: InkWell(
                    onTap: _selectStartDate,
                    child: InputDecorator(
                      decoration: const InputDecoration(
                        labelText: 'Start Date',
                        border: OutlineInputBorder(),
                        suffixIcon: Icon(Icons.calendar_today),
                      ),
                      child: Text(
                        _startDate != null
                            ? formatDateOnly(_startDate!)
                            : 'Select date',
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: InkWell(
                    onTap: _selectEndDate,
                    child: InputDecorator(
                      decoration: const InputDecoration(
                        labelText: 'End Date',
                        border: OutlineInputBorder(),
                        suffixIcon: Icon(Icons.calendar_today),
                      ),
                      child: Text(
                        _endDate != null
                            ? formatDateOnly(_endDate!)
                            : 'Select date',
                      ),
                    ),
                  ),
                ),
              ],
            ),
            if (_startDate != null || _endDate != null) ...[
              const SizedBox(height: 8),
              TextButton(
                onPressed: _clearDateRange,
                child: const Text('Clear Date Range'),
              ),
            ],
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('Cancel'),
        ),
        TextButton(onPressed: _clearAllFilters, child: const Text('Clear All')),
        ElevatedButton(onPressed: _applyFilters, child: const Text('Apply')),
      ],
    );
  }

  Future<void> _selectStartDate() async {
    final selectedDate = await showDatePicker(
      context: context,
      initialDate:
          _startDate ?? DateTime.now().subtract(const Duration(days: 30)),
      firstDate: DateTime.now().subtract(const Duration(days: 365)),
      lastDate: _endDate ?? DateTime.now(),
    );

    if (selectedDate != null) {
      setState(() {
        _startDate = selectedDate;
      });
    }
  }

  Future<void> _selectEndDate() async {
    final selectedDate = await showDatePicker(
      context: context,
      initialDate: _endDate ?? DateTime.now(),
      firstDate:
          _startDate ?? DateTime.now().subtract(const Duration(days: 365)),
      lastDate: DateTime.now(),
    );

    if (selectedDate != null) {
      setState(() {
        _endDate = selectedDate;
      });
    }
  }

  void _clearDateRange() {
    setState(() {
      _startDate = null;
      _endDate = null;
    });
  }

  void _clearAllFilters() {
    Navigator.of(context).pop(const PackageDeliveryFilter());
  }

  void _applyFilters() {
    final filter = PackageDeliveryFilter(
      searchTerm:
          _searchController.text.trim().isEmpty
              ? null
              : _searchController.text.trim(),
      status: _selectedStatus,
      startDate: _startDate,
      endDate: _endDate,
    );

    Navigator.of(context).pop(filter);
  }
}
