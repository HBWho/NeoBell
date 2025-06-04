import 'package:equatable/equatable.dart';

import '../../domain/entities/create_package_delivery.dart';
import '../../domain/entities/package_delivery_filter.dart';
import '../../domain/entities/update_package_delivery.dart';

abstract class PackageDeliveryEvent extends Equatable {
  const PackageDeliveryEvent();

  @override
  List<Object?> get props => [];
}

class LoadPackageDeliveries extends PackageDeliveryEvent {
  final PackageDeliveryFilter? filter;
  final int? limit;
  final String? lastEvaluatedKey;
  final bool refresh;

  const LoadPackageDeliveries({
    this.filter,
    this.limit,
    this.lastEvaluatedKey,
    this.refresh = false,
  });

  @override
  List<Object?> get props => [filter, limit, lastEvaluatedKey, refresh];
}

class LoadPackageDeliveryDetails extends PackageDeliveryEvent {
  final String orderId;

  const LoadPackageDeliveryDetails(this.orderId);

  @override
  List<Object?> get props => [orderId];
}

class CreatePackageDeliveryEvent extends PackageDeliveryEvent {
  final CreatePackageDelivery delivery;

  const CreatePackageDeliveryEvent(this.delivery);

  @override
  List<Object?> get props => [delivery];
}

class UpdatePackageDeliveryEvent extends PackageDeliveryEvent {
  final String orderId;
  final UpdatePackageDelivery delivery;

  const UpdatePackageDeliveryEvent({
    required this.orderId,
    required this.delivery,
  });

  @override
  List<Object?> get props => [orderId, delivery];
}

class DeletePackageDeliveryEvent extends PackageDeliveryEvent {
  final String orderId;

  const DeletePackageDeliveryEvent(this.orderId);

  @override
  List<Object?> get props => [orderId];
}

class ApplyFilterEvent extends PackageDeliveryEvent {
  final PackageDeliveryFilter filter;

  const ApplyFilterEvent(this.filter);

  @override
  List<Object?> get props => [filter];
}

class ClearFilterEvent extends PackageDeliveryEvent {
  const ClearFilterEvent();
}

class RefreshPackageDeliveries extends PackageDeliveryEvent {
  const RefreshPackageDeliveries();
}

class LoadMorePackageDeliveries extends PackageDeliveryEvent {
  const LoadMorePackageDeliveries();
}
