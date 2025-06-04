import 'package:flutter/foundation.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:equatable/equatable.dart';

import '../../domain/entities/activity_log.dart';
import '../../domain/entities/activity_log_filter.dart';
import '../../domain/use_cases/get_activity_logs.dart';

part 'activity_log_event.dart';
part 'activity_log_state.dart';

class ActivityLogBloc extends Bloc<ActivityLogEvent, ActivityLogState> {
  final GetActivityLogs _getActivityLogs;

  ActivityLogBloc({required GetActivityLogs getActivityLogs})
    : _getActivityLogs = getActivityLogs,
      super(ActivityLogInitial()) {
    on<LoadActivityLogs>(_onLoadActivityLogs);
    on<LoadMoreActivityLogs>(_onLoadMoreActivityLogs);
    on<SelectActivityLogFromCache>(_onSelectActivityLogFromCache);
    on<RefreshActivityLogs>(_onRefreshActivityLogs);
    on<ApplyActivityLogFilter>(_onApplyActivityLogFilter);
  }

  Future<void> _onLoadActivityLogs(
    LoadActivityLogs event,
    Emitter<ActivityLogState> emit,
  ) async {
    emit(
      ActivityLogLoading(
        activityLogs: state.activityLogs,
        currentFilter: event.filter,
      ),
    );

    final result = await _getActivityLogs(event.filter);

    result.fold(
      (failure) => emit(
        ActivityLogFailure(
          message: failure.message,
          activityLogs: state.activityLogs,
          currentFilter: state.currentFilter,
        ),
      ),
      (response) => emit(
        ActivityLogLoaded(
          activityLogs: response.items,
          lastEvaluatedKey: response.lastEvaluatedKey,
          hasMore: response.hasMore,
          currentFilter: event.filter,
        ),
      ),
    );
  }

  Future<void> _onLoadMoreActivityLogs(
    LoadMoreActivityLogs event,
    Emitter<ActivityLogState> emit,
  ) async {
    if (state is! ActivityLogLoaded) return;

    final currentState = state as ActivityLogLoaded;
    if (!currentState.hasMore || currentState.lastEvaluatedKey == null) return;

    emit(
      ActivityLogLoadingMore(
        activityLogs: currentState.activityLogs,
        lastEvaluatedKey: currentState.lastEvaluatedKey,
        hasMore: currentState.hasMore,
        currentFilter: currentState.currentFilter,
      ),
    );

    final filter = currentState.currentFilter.copyWith(
      lastEvaluatedKey: currentState.lastEvaluatedKey,
    );

    final result = await _getActivityLogs(filter);

    result.fold(
      (failure) => emit(
        ActivityLogFailure(
          message: failure.message,
          activityLogs: currentState.activityLogs,
          currentFilter: currentState.currentFilter,
        ),
      ),
      (response) => emit(
        ActivityLogLoaded(
          activityLogs: [...currentState.activityLogs, ...response.items],
          lastEvaluatedKey: response.lastEvaluatedKey,
          hasMore: response.hasMore,
          currentFilter: currentState.currentFilter,
        ),
      ),
    );
  }

  void _onSelectActivityLogFromCache(
    SelectActivityLogFromCache event,
    Emitter<ActivityLogState> emit,
  ) {
    try {
      final activityLog = state.activityLogs.firstWhere(
        (log) =>
            log.logSourceId == event.logSourceId &&
            log.timestampUuid == event.timestampUuid,
      );

      emit(
        ActivityLogDetailsLoaded(
          currentActivityLog: activityLog,
          activityLogs: state.activityLogs,
          currentFilter: state.currentFilter,
        ),
      );
    } catch (e) {
      emit(
        ActivityLogFailure(
          message: 'Activity log not found in cache',
          activityLogs: state.activityLogs,
          currentFilter: state.currentFilter,
        ),
      );
    }
  }

  Future<void> _onRefreshActivityLogs(
    RefreshActivityLogs event,
    Emitter<ActivityLogState> emit,
  ) async {
    final filter = state.currentFilter.copyWith(lastEvaluatedKey: null);
    add(LoadActivityLogs(filter: filter));
  }

  Future<void> _onApplyActivityLogFilter(
    ApplyActivityLogFilter event,
    Emitter<ActivityLogState> emit,
  ) async {
    final filter = event.filter.copyWith(lastEvaluatedKey: null);
    add(LoadActivityLogs(filter: filter));
  }
}
