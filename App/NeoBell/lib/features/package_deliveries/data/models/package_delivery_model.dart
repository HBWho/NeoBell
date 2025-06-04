import '../../domain/entities/package_delivery.dart';

class PackageDeliveryModel extends PackageDelivery {
  const PackageDeliveryModel({
    required super.userId,
    required super.orderId,
    required super.itemDescription,
    super.trackingNumber,
    super.carrier,
    required super.status,
    super.sbcIdReceivedAt,
    required super.addedAt,
    required super.expectedDate,
    super.receivedAtTimestamp,
  });

  factory PackageDeliveryModel.fromJson(Map<String, dynamic> json) {
    return PackageDeliveryModel(
      userId: json['user_id'] as String,
      orderId: json['order_id'] as String,
      itemDescription: json['item_description'] as String,
      trackingNumber: json['tracking_number'] as String?,
      carrier: json['carrier'] as String?,
      status: PackageDeliveryStatus.fromApiValue(json['status'] as String),
      sbcIdReceivedAt: json['sbc_id_received_at'] as String?,
      addedAt: DateTime.parse(json['added_at'] as String),
      expectedDate: DateTime.parse(json['expected_date'] as String),
      receivedAtTimestamp:
          json['received_at_timestamp'] != null
              ? DateTime.parse(json['received_at_timestamp'] as String)
              : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'user_id': userId,
      'order_id': orderId,
      'item_description': itemDescription,
      'tracking_number': trackingNumber,
      'carrier': carrier,
      'status': status.apiValue,
      'sbc_id_received_at': sbcIdReceivedAt,
      'added_at': addedAt.toIso8601String(),
      'expected_date': expectedDate.toIso8601String().split('T')[0],
      'received_at_timestamp': receivedAtTimestamp?.toIso8601String(),
    };
  }

  PackageDeliveryModel copyWith({
    String? userId,
    String? orderId,
    String? itemDescription,
    String? trackingNumber,
    String? carrier,
    PackageDeliveryStatus? status,
    String? sbcIdReceivedAt,
    DateTime? addedAt,
    DateTime? expectedDate,
    DateTime? receivedAtTimestamp,
  }) {
    return PackageDeliveryModel(
      userId: userId ?? this.userId,
      orderId: orderId ?? this.orderId,
      itemDescription: itemDescription ?? this.itemDescription,
      trackingNumber: trackingNumber ?? this.trackingNumber,
      carrier: carrier ?? this.carrier,
      status: status ?? this.status,
      sbcIdReceivedAt: sbcIdReceivedAt ?? this.sbcIdReceivedAt,
      addedAt: addedAt ?? this.addedAt,
      expectedDate: expectedDate ?? this.expectedDate,
      receivedAtTimestamp: receivedAtTimestamp ?? this.receivedAtTimestamp,
    );
  }
}
