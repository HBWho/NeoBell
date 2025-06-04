import 'package:equatable/equatable.dart';

import '../../domain/entities/package_delivery.dart';
import '../../domain/entities/package_delivery_filter.dart';

abstract class PackageDeliveryState extends Equatable {
  const PackageDeliveryState();

  @override
  List<Object?> get props => [];
}

class PackageDeliveryInitial extends PackageDeliveryState {
  const PackageDeliveryInitial();
}

class PackageDeliveryLoading extends PackageDeliveryState {
  const PackageDeliveryLoading();
}

class PackageDeliveryLoadingMore extends PackageDeliveryState {
  final List<PackageDelivery> currentDeliveries;
  final PackageDeliveryFilter? currentFilter;

  const PackageDeliveryLoadingMore({
    required this.currentDeliveries,
    this.currentFilter,
  });

  @override
  List<Object?> get props => [currentDeliveries, currentFilter];
}

class PackageDeliveryLoaded extends PackageDeliveryState {
  final List<PackageDelivery> deliveries;
  final PackageDeliveryFilter? filter;
  final bool hasReachedMax;
  final String? lastEvaluatedKey;

  const PackageDeliveryLoaded({
    required this.deliveries,
    this.filter,
    this.hasReachedMax = false,
    this.lastEvaluatedKey,
  });

  @override
  List<Object?> get props => [
    deliveries,
    filter,
    hasReachedMax,
    lastEvaluatedKey,
  ];

  PackageDeliveryLoaded copyWith({
    List<PackageDelivery>? deliveries,
    PackageDeliveryFilter? filter,
    bool? hasReachedMax,
    String? lastEvaluatedKey,
  }) {
    return PackageDeliveryLoaded(
      deliveries: deliveries ?? this.deliveries,
      filter: filter ?? this.filter,
      hasReachedMax: hasReachedMax ?? this.hasReachedMax,
      lastEvaluatedKey: lastEvaluatedKey ?? this.lastEvaluatedKey,
    );
  }
}

class PackageDeliveryError extends PackageDeliveryState {
  final String message;
  final List<PackageDelivery>? previousDeliveries;
  final PackageDeliveryFilter? previousFilter;

  const PackageDeliveryError({
    required this.message,
    this.previousDeliveries,
    this.previousFilter,
  });

  @override
  List<Object?> get props => [message, previousDeliveries, previousFilter];
}

class PackageDeliveryDetailsLoading extends PackageDeliveryState {
  const PackageDeliveryDetailsLoading();
}

class PackageDeliveryDetailsLoaded extends PackageDeliveryState {
  final PackageDelivery delivery;

  const PackageDeliveryDetailsLoaded(this.delivery);

  @override
  List<Object?> get props => [delivery];
}

class PackageDeliveryOperationLoading extends PackageDeliveryState {
  final String operation;
  final List<PackageDelivery>? currentDeliveries;

  const PackageDeliveryOperationLoading({
    required this.operation,
    this.currentDeliveries,
  });

  @override
  List<Object?> get props => [operation, currentDeliveries];
}

class PackageDeliveryOperationSuccess extends PackageDeliveryState {
  final String message;
  final PackageDelivery? delivery;

  const PackageDeliveryOperationSuccess({required this.message, this.delivery});

  @override
  List<Object?> get props => [message, delivery];
}
