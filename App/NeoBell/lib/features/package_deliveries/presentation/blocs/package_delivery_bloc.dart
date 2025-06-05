import 'package:flutter_bloc/flutter_bloc.dart';

import '../../domain/entities/package_delivery.dart';
import '../../domain/entities/package_delivery_filter.dart';
import '../../domain/use_cases/create_package_delivery.dart';
import '../../domain/use_cases/delete_package_delivery.dart';
import '../../domain/use_cases/get_package_deliveries.dart';
import '../../domain/use_cases/get_package_delivery_details.dart';
import '../../domain/use_cases/update_package_delivery.dart';
import 'package_delivery_event.dart';
import 'package_delivery_state.dart';

class PackageDeliveryBloc
    extends Bloc<PackageDeliveryEvent, PackageDeliveryState> {
  final GetPackageDeliveries _getPackageDeliveries;
  final GetPackageDeliveryDetails _getPackageDeliveryDetails;
  final CreatePackageDeliveryUseCase _createPackageDelivery;
  final UpdatePackageDeliveryUseCase _updatePackageDelivery;
  final DeletePackageDelivery _deletePackageDelivery;

  static const int _defaultLimit = 20;

  PackageDeliveryBloc({
    required GetPackageDeliveries getPackageDeliveries,
    required GetPackageDeliveryDetails getPackageDeliveryDetails,
    required CreatePackageDeliveryUseCase createPackageDelivery,
    required UpdatePackageDeliveryUseCase updatePackageDelivery,
    required DeletePackageDelivery deletePackageDelivery,
  }) : _getPackageDeliveries = getPackageDeliveries,
       _getPackageDeliveryDetails = getPackageDeliveryDetails,
       _createPackageDelivery = createPackageDelivery,
       _updatePackageDelivery = updatePackageDelivery,
       _deletePackageDelivery = deletePackageDelivery,
       super(const PackageDeliveryInitial()) {
    on<LoadPackageDeliveries>(_onLoadPackageDeliveries);
    on<LoadPackageDeliveryDetails>(_onLoadPackageDeliveryDetails);
    on<CreatePackageDeliveryEvent>(_onCreatePackageDelivery);
    on<UpdatePackageDeliveryEvent>(_onUpdatePackageDelivery);
    on<DeletePackageDeliveryEvent>(_onDeletePackageDelivery);
    on<ApplyFilterEvent>(_onApplyFilter);
    on<ClearFilterEvent>(_onClearFilter);
    on<RefreshPackageDeliveries>(_onRefreshPackageDeliveries);
    on<LoadMorePackageDeliveries>(_onLoadMorePackageDeliveries);
  }

  Future<void> _onLoadPackageDeliveries(
    LoadPackageDeliveries event,
    Emitter<PackageDeliveryState> emit,
  ) async {
    if (event.refresh || state is! PackageDeliveryLoaded) {
      emit(
        PackageDeliveryLoading(
          deliveries: state.deliveries,
          currentDelivery: state.currentDelivery,
        ),
      );
    } else if (event.lastEvaluatedKey != null) {
      final currentState = state as PackageDeliveryLoaded;
      emit(
        PackageDeliveryLoadingMore(
          deliveries: currentState.deliveries,
          currentFilter: currentState.filter,
          currentDelivery: currentState.currentDelivery,
        ),
      );
    }

    final result = await _getPackageDeliveries(
      GetPackageDeliveriesParams(
        filter: event.filter,
        limit: event.limit ?? _defaultLimit,
        lastEvaluatedKey: event.lastEvaluatedKey,
      ),
    );

    result.fold(
      (failure) {
        if (state is PackageDeliveryLoadingMore) {
          final loadingState = state as PackageDeliveryLoadingMore;
          emit(
            PackageDeliveryError(
              message: failure.message,
              deliveries: loadingState.deliveries,
              previousFilter: loadingState.currentFilter,
              currentDelivery: loadingState.currentDelivery,
            ),
          );
        } else {
          emit(PackageDeliveryError(message: failure.message));
        }
      },
      (deliveries) {
        if (state is PackageDeliveryLoadingMore) {
          final loadingState = state as PackageDeliveryLoadingMore;
          final allDeliveries = [...loadingState.deliveries, ...deliveries];
          emit(
            PackageDeliveryLoaded(
              deliveries: allDeliveries,
              filter: event.filter,
              hasReachedMax: deliveries.length < (event.limit ?? _defaultLimit),
              lastEvaluatedKey:
                  deliveries.isNotEmpty ? deliveries.last.orderId : null,
              currentDelivery: loadingState.currentDelivery,
            ),
          );
        } else {
          emit(
            PackageDeliveryLoaded(
              deliveries: deliveries,
              filter: event.filter,
              hasReachedMax: deliveries.length < (event.limit ?? _defaultLimit),
              lastEvaluatedKey:
                  deliveries.isNotEmpty ? deliveries.last.orderId : null,
              currentDelivery: state.currentDelivery,
            ),
          );
        }
      },
    );
  }

  Future<void> _onLoadPackageDeliveryDetails(
    LoadPackageDeliveryDetails event,
    Emitter<PackageDeliveryState> emit,
  ) async {
    // Check if delivery is already cached in the state
    final cachedDelivery =
        state.deliveries
            .where((delivery) => delivery.orderId == event.orderId)
            .firstOrNull;

    if (cachedDelivery != null) {
      emit(
        PackageDeliveryDetailsLoaded(
          delivery: cachedDelivery,
          deliveries: state.deliveries,
        ),
      );
      return;
    }

    emit(
      PackageDeliveryDetailsLoading(
        deliveries: state.deliveries,
        currentDelivery: state.currentDelivery,
      ),
    );

    final result = await _getPackageDeliveryDetails(event.orderId);

    result.fold(
      (failure) => emit(
        PackageDeliveryError(
          message: failure.message,
          deliveries: state.deliveries,
          currentDelivery: state.currentDelivery,
        ),
      ),
      (delivery) {
        // Update the cached deliveries with the detailed delivery
        List<PackageDelivery> updatedDeliveries =
            state.deliveries
                .map((d) => d.orderId == delivery.orderId ? delivery : d)
                .toList();
        if (!updatedDeliveries.any((d) => d.orderId == delivery.orderId)) {
          updatedDeliveries.add(delivery);
        }
        emit(
          PackageDeliveryDetailsLoaded(
            delivery: delivery,
            deliveries: updatedDeliveries,
          ),
        );
      },
    );
  }

  Future<void> _onCreatePackageDelivery(
    CreatePackageDeliveryEvent event,
    Emitter<PackageDeliveryState> emit,
  ) async {
    emit(
      PackageDeliveryOperationLoading(
        operation: 'Creating package delivery',
        deliveries: state.deliveries,
        currentDelivery: state.currentDelivery,
      ),
    );

    final result = await _createPackageDelivery(event.delivery);

    result.fold(
      (failure) => emit(
        PackageDeliveryError(
          message: failure.message,
          deliveries: state.deliveries,
          currentDelivery: state.currentDelivery,
        ),
      ),
      (delivery) {
        emit(
          PackageDeliveryOperationSuccess(
            message: 'Package delivery created successfully',
            delivery: delivery,
            deliveries: state.deliveries,
            currentDelivery: state.currentDelivery,
          ),
        );
        add(const RefreshPackageDeliveries());
      },
    );
  }

  Future<void> _onUpdatePackageDelivery(
    UpdatePackageDeliveryEvent event,
    Emitter<PackageDeliveryState> emit,
  ) async {
    emit(
      PackageDeliveryOperationLoading(
        operation: 'Updating package delivery',
        deliveries: state.deliveries,
        currentDelivery: state.currentDelivery,
      ),
    );

    final result = await _updatePackageDelivery(
      UpdatePackageDeliveryParams(
        orderId: event.orderId,
        update: event.delivery,
      ),
    );

    result.fold(
      (failure) => emit(
        PackageDeliveryError(
          message: failure.message,
          deliveries: state.deliveries,
          currentDelivery: state.currentDelivery,
        ),
      ),
      (delivery) {
        // Update the cached deliveries with the updated delivery
        final updatedDeliveries =
            state.deliveries
                .map((d) => d.orderId == delivery.orderId ? delivery : d)
                .toList();

        final newCurrentDelivery =
            state.currentDelivery?.orderId == delivery.orderId
                ? delivery
                : state.currentDelivery;

        emit(
          PackageDeliveryOperationSuccess(
            message: 'Package delivery updated successfully',
            delivery: delivery,
            deliveries: updatedDeliveries,
            currentDelivery: newCurrentDelivery,
          ),
        );
        add(const RefreshPackageDeliveries());
      },
    );
  }

  Future<void> _onDeletePackageDelivery(
    DeletePackageDeliveryEvent event,
    Emitter<PackageDeliveryState> emit,
  ) async {
    emit(
      PackageDeliveryOperationLoading(
        operation: 'Deleting package delivery',
        deliveries: state.deliveries,
        currentDelivery: state.currentDelivery,
      ),
    );

    final result = await _deletePackageDelivery(event.orderId);

    result.fold(
      (failure) => emit(
        PackageDeliveryError(
          message: failure.message,
          deliveries: state.deliveries,
          currentDelivery: state.currentDelivery,
        ),
      ),
      (_) {
        // Remove the deleted delivery from the cache
        final updatedDeliveries =
            state.deliveries.where((d) => d.orderId != event.orderId).toList();

        final newCurrentDelivery =
            state.currentDelivery?.orderId == event.orderId
                ? null
                : state.currentDelivery;

        emit(
          PackageDeliveryOperationSuccess(
            message: 'Package delivery deleted successfully',
            deliveries: updatedDeliveries,
            currentDelivery: newCurrentDelivery,
          ),
        );
        add(const RefreshPackageDeliveries());
      },
    );
  }

  Future<void> _onApplyFilter(
    ApplyFilterEvent event,
    Emitter<PackageDeliveryState> emit,
  ) async {
    add(LoadPackageDeliveries(filter: event.filter, refresh: true));
  }

  Future<void> _onClearFilter(
    ClearFilterEvent event,
    Emitter<PackageDeliveryState> emit,
  ) async {
    add(const LoadPackageDeliveries(refresh: true));
  }

  Future<void> _onRefreshPackageDeliveries(
    RefreshPackageDeliveries event,
    Emitter<PackageDeliveryState> emit,
  ) async {
    PackageDeliveryFilter? currentFilter;
    if (state is PackageDeliveryLoaded) {
      currentFilter = (state as PackageDeliveryLoaded).filter;
    }
    add(LoadPackageDeliveries(filter: currentFilter, refresh: true));
  }

  Future<void> _onLoadMorePackageDeliveries(
    LoadMorePackageDeliveries event,
    Emitter<PackageDeliveryState> emit,
  ) async {
    if (state is PackageDeliveryLoaded) {
      final currentState = state as PackageDeliveryLoaded;
      if (!currentState.hasReachedMax &&
          currentState.lastEvaluatedKey != null) {
        add(
          LoadPackageDeliveries(
            filter: currentState.filter,
            lastEvaluatedKey: currentState.lastEvaluatedKey,
          ),
        );
      }
    }
  }
}
