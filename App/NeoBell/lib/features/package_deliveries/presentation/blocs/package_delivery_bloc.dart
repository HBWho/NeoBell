import 'package:flutter_bloc/flutter_bloc.dart';

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
      emit(const PackageDeliveryLoading());
    } else if (event.lastEvaluatedKey != null) {
      final currentState = state as PackageDeliveryLoaded;
      emit(
        PackageDeliveryLoadingMore(
          currentDeliveries: currentState.deliveries,
          currentFilter: currentState.filter,
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
              previousDeliveries: loadingState.currentDeliveries,
              previousFilter: loadingState.currentFilter,
            ),
          );
        } else {
          emit(PackageDeliveryError(message: failure.message));
        }
      },
      (deliveries) {
        if (state is PackageDeliveryLoadingMore) {
          final loadingState = state as PackageDeliveryLoadingMore;
          final allDeliveries = [
            ...loadingState.currentDeliveries,
            ...deliveries,
          ];
          emit(
            PackageDeliveryLoaded(
              deliveries: allDeliveries,
              filter: event.filter,
              hasReachedMax: deliveries.length < (event.limit ?? _defaultLimit),
              lastEvaluatedKey:
                  deliveries.isNotEmpty ? deliveries.last.orderId : null,
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
    emit(const PackageDeliveryDetailsLoading());

    final result = await _getPackageDeliveryDetails(event.orderId);

    result.fold(
      (failure) => emit(PackageDeliveryError(message: failure.message)),
      (delivery) => emit(PackageDeliveryDetailsLoaded(delivery)),
    );
  }

  Future<void> _onCreatePackageDelivery(
    CreatePackageDeliveryEvent event,
    Emitter<PackageDeliveryState> emit,
  ) async {
    emit(
      const PackageDeliveryOperationLoading(
        operation: 'Creating package delivery',
      ),
    );

    final result = await _createPackageDelivery(event.delivery);

    result.fold(
      (failure) => emit(PackageDeliveryError(message: failure.message)),
      (delivery) {
        emit(
          PackageDeliveryOperationSuccess(
            message: 'Package delivery created successfully',
            delivery: delivery,
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
      const PackageDeliveryOperationLoading(
        operation: 'Updating package delivery',
      ),
    );

    final result = await _updatePackageDelivery(
      UpdatePackageDeliveryParams(
        orderId: event.orderId,
        update: event.delivery,
      ),
    );

    result.fold(
      (failure) => emit(PackageDeliveryError(message: failure.message)),
      (delivery) {
        emit(
          PackageDeliveryOperationSuccess(
            message: 'Package delivery updated successfully',
            delivery: delivery,
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
      const PackageDeliveryOperationLoading(
        operation: 'Deleting package delivery',
      ),
    );

    final result = await _deletePackageDelivery(event.orderId);

    result.fold(
      (failure) => emit(PackageDeliveryError(message: failure.message)),
      (_) {
        emit(
          const PackageDeliveryOperationSuccess(
            message: 'Package delivery deleted successfully',
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
