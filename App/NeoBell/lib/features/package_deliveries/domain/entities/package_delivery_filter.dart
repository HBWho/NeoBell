import 'package:equatable/equatable.dart';
import 'package_delivery.dart';

class PackageDeliveryFilter extends Equatable {
  final PackageDeliveryStatus? status;
  final DateTime? startDate;
  final DateTime? endDate;
  final String? searchTerm;

  const PackageDeliveryFilter({
    this.status,
    this.startDate,
    this.endDate,
    this.searchTerm,
  });

  PackageDeliveryFilter copyWith({
    PackageDeliveryStatus? status,
    DateTime? startDate,
    DateTime? endDate,
    String? searchTerm,
  }) {
    return PackageDeliveryFilter(
      status: status ?? this.status,
      startDate: startDate ?? this.startDate,
      endDate: endDate ?? this.endDate,
      searchTerm: searchTerm ?? this.searchTerm,
    );
  }

  bool get hasActiveFilters {
    return status != null ||
        startDate != null ||
        endDate != null ||
        (searchTerm != null && searchTerm!.trim().isNotEmpty);
  }

  PackageDeliveryFilter clear() {
    return const PackageDeliveryFilter();
  }

  Map<String, dynamic> toQueryParameters() {
    final Map<String, dynamic> params = {};

    if (status != null) {
      params['status'] = status!.apiValue;
    }

    if (startDate != null) {
      params['start_date'] = startDate!.toIso8601String().split('T')[0];
    }

    if (endDate != null) {
      params['end_date'] = endDate!.toIso8601String().split('T')[0];
    }

    if (searchTerm != null && searchTerm!.trim().isNotEmpty) {
      params['search'] = searchTerm!.trim();
    }

    return params;
  }

  @override
  List<Object?> get props => [status, startDate, endDate, searchTerm];
}
