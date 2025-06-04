import 'package:equatable/equatable.dart';
import 'package_delivery.dart';

class UpdatePackageDelivery extends Equatable {
  final String? itemDescription;
  final String? trackingNumber;
  final String? carrier;
  final PackageDeliveryStatus? status;
  final DateTime? expectedDate;

  const UpdatePackageDelivery({
    this.itemDescription,
    this.trackingNumber,
    this.carrier,
    this.status,
    this.expectedDate,
  });

  Map<String, dynamic> toJson() {
    final Map<String, dynamic> json = {};

    if (itemDescription != null && itemDescription!.trim().isNotEmpty) {
      json['item_description'] = itemDescription!.trim();
    }

    if (trackingNumber != null) {
      json['tracking_number'] =
          trackingNumber!.trim().isEmpty ? null : trackingNumber!.trim();
    }

    if (carrier != null) {
      json['carrier'] = carrier!.trim().isEmpty ? null : carrier!.trim();
    }

    if (status != null) {
      json['status'] = status!.apiValue;
    }

    if (expectedDate != null) {
      json['expected_date'] = expectedDate!.toIso8601String().split('T')[0];
    }

    return json;
  }

  bool get hasUpdates {
    return itemDescription != null ||
        trackingNumber != null ||
        carrier != null ||
        status != null ||
        expectedDate != null;
  }

  @override
  List<Object?> get props => [
    itemDescription,
    trackingNumber,
    carrier,
    status,
    expectedDate,
  ];
}
