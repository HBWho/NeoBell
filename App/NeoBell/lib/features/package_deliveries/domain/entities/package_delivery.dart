import 'package:equatable/equatable.dart';

class PackageDelivery extends Equatable {
  final String userId;
  final String orderId;
  final String itemDescription;
  final String? trackingNumber;
  final String? carrier;
  final PackageDeliveryStatus status;
  final String? sbcIdReceivedAt;
  final DateTime addedAt;
  final DateTime expectedDate;
  final DateTime? receivedAtTimestamp;

  const PackageDelivery({
    required this.userId,
    required this.orderId,
    required this.itemDescription,
    this.trackingNumber,
    this.carrier,
    required this.status,
    this.sbcIdReceivedAt,
    required this.addedAt,
    required this.expectedDate,
    this.receivedAtTimestamp,
  });

  PackageDelivery copyWith({
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
    return PackageDelivery(
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

  bool get isReceived =>
      status == PackageDeliveryStatus.inBox1 ||
      status == PackageDeliveryStatus.inBox2;

  bool get isRetrieved => status == PackageDeliveryStatus.retrievedByUser;

  bool get isPending => status == PackageDeliveryStatus.pending;

  bool get isCancelled => status == PackageDeliveryStatus.cancelled;

  @override
  List<Object?> get props => [
    userId,
    orderId,
    itemDescription,
    trackingNumber,
    carrier,
    status,
    sbcIdReceivedAt,
    addedAt,
    expectedDate,
    receivedAtTimestamp,
  ];
}

enum PackageDeliveryStatus {
  pending,
  inBox1,
  inBox2,
  retrievedByUser,
  cancelled;

  String get displayName {
    switch (this) {
      case PackageDeliveryStatus.pending:
        return 'Pending';
      case PackageDeliveryStatus.inBox1:
        return 'In Box 1';
      case PackageDeliveryStatus.inBox2:
        return 'In Box 2';
      case PackageDeliveryStatus.retrievedByUser:
        return 'Retrieved';
      case PackageDeliveryStatus.cancelled:
        return 'Cancelled';
    }
  }

  String get apiValue {
    switch (this) {
      case PackageDeliveryStatus.pending:
        return 'pending';
      case PackageDeliveryStatus.inBox1:
        return 'in_box1';
      case PackageDeliveryStatus.inBox2:
        return 'in_box2';
      case PackageDeliveryStatus.retrievedByUser:
        return 'retrieved_by_user';
      case PackageDeliveryStatus.cancelled:
        return 'cancelled';
    }
  }

  static PackageDeliveryStatus fromApiValue(String value) {
    switch (value) {
      case 'pending':
        return PackageDeliveryStatus.pending;
      case 'in_box1':
        return PackageDeliveryStatus.inBox1;
      case 'in_box2':
        return PackageDeliveryStatus.inBox2;
      case 'retrieved_by_user':
        return PackageDeliveryStatus.retrievedByUser;
      case 'cancelled':
        return PackageDeliveryStatus.cancelled;
      default:
        return PackageDeliveryStatus.pending;
    }
  }
}
