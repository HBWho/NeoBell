import 'package:equatable/equatable.dart';

import '../../domain/entities/package_delivery.dart';
import '../../domain/entities/package_delivery_filter.dart';

abstract class PackageDeliveryState extends Equatable {
  final List<PackageDelivery> deliveries;
  final PackageDelivery? currentDelivery;

  const PackageDeliveryState({
    this.deliveries = const [],
    this.currentDelivery,
  });

  @override
  List<Object?> get props => [deliveries, currentDelivery];
}

class PackageDeliveryInitial extends PackageDeliveryState {
  const PackageDeliveryInitial();
}

class PackageDeliveryLoading extends PackageDeliveryState {
  const PackageDeliveryLoading({super.deliveries, super.currentDelivery});
}

class PackageDeliveryLoadingMore extends PackageDeliveryState {
  final PackageDeliveryFilter? currentFilter;

  const PackageDeliveryLoadingMore({
    required super.deliveries,
    this.currentFilter,
    super.currentDelivery,
  });

  @override
  List<Object?> get props => [deliveries, currentFilter, currentDelivery];
}

class PackageDeliveryLoaded extends PackageDeliveryState {
  final PackageDeliveryFilter? filter;
  final bool hasReachedMax;
  final String? lastEvaluatedKey;

  const PackageDeliveryLoaded({
    required super.deliveries,
    this.filter,
    this.hasReachedMax = false,
    this.lastEvaluatedKey,
    super.currentDelivery,
  });

  @override
  List<Object?> get props => [
    deliveries,
    filter,
    hasReachedMax,
    lastEvaluatedKey,
    currentDelivery,
  ];

  PackageDeliveryLoaded copyWith({
    List<PackageDelivery>? deliveries,
    PackageDeliveryFilter? filter,
    bool? hasReachedMax,
    String? lastEvaluatedKey,
    PackageDelivery? currentDelivery,
  }) {
    return PackageDeliveryLoaded(
      deliveries: deliveries ?? this.deliveries,
      filter: filter ?? this.filter,
      hasReachedMax: hasReachedMax ?? this.hasReachedMax,
      lastEvaluatedKey: lastEvaluatedKey ?? this.lastEvaluatedKey,
      currentDelivery: currentDelivery ?? this.currentDelivery,
    );
  }
}

class PackageDeliveryError extends PackageDeliveryState {
  final String message;
  final PackageDeliveryFilter? previousFilter;

  const PackageDeliveryError({
    required this.message,
    super.deliveries = const [],
    this.previousFilter,
    super.currentDelivery,
  });

  @override
  List<Object?> get props => [
    message,
    deliveries,
    previousFilter,
    currentDelivery,
  ];
}

class PackageDeliveryDetailsLoading extends PackageDeliveryState {
  const PackageDeliveryDetailsLoading({
    super.deliveries,
    super.currentDelivery,
  });
}

class PackageDeliveryDetailsLoaded extends PackageDeliveryState {
  const PackageDeliveryDetailsLoaded({
    required PackageDelivery delivery,
    super.deliveries,
  }) : super(currentDelivery: delivery);

  PackageDelivery get delivery => currentDelivery!;

  @override
  List<Object?> get props => [currentDelivery, deliveries];
}

class PackageDeliveryOperationLoading extends PackageDeliveryState {
  final String operation;

  const PackageDeliveryOperationLoading({
    required this.operation,
    super.deliveries = const [],
    super.currentDelivery,
  });

  @override
  List<Object?> get props => [operation, deliveries, currentDelivery];
}

class PackageDeliveryOperationSuccess extends PackageDeliveryState {
  final String message;
  final PackageDelivery? delivery;

  const PackageDeliveryOperationSuccess({
    required this.message,
    this.delivery,
    super.deliveries = const [],
    super.currentDelivery,
  });

  @override
  List<Object?> get props => [message, delivery, deliveries, currentDelivery];
}
