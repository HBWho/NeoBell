import 'package:equatable/equatable.dart';

class CreatePackageDelivery extends Equatable {
  final String orderId;
  final String itemDescription;
  final String? trackingNumber;
  final String? carrier;
  final DateTime expectedDate;

  const CreatePackageDelivery({
    required this.orderId,
    required this.itemDescription,
    this.trackingNumber,
    this.carrier,
    required this.expectedDate,
  });

  Map<String, dynamic> toJson() {
    return {
      'order_id': orderId,
      'item_description': itemDescription,
      if (trackingNumber != null && trackingNumber!.trim().isNotEmpty)
        'tracking_number': trackingNumber!.trim(),
      if (carrier != null && carrier!.trim().isNotEmpty)
        'carrier': carrier!.trim(),
      'expected_date':
          expectedDate.toIso8601String().split('T')[0], // YYYY-MM-DD format
    };
  }

  @override
  List<Object?> get props => [
    orderId,
    itemDescription,
    trackingNumber,
    carrier,
    expectedDate,
  ];
}
