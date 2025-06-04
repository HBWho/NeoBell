part of 'activity_log_bloc.dart';

abstract class ActivityLogState extends Equatable {
  final List<ActivityLog> activityLogs;
  final ActivityLogFilter currentFilter;

  const ActivityLogState({
    this.activityLogs = const [],
    this.currentFilter = const ActivityLogFilter(),
  });

  @override
  List<Object?> get props => [activityLogs, currentFilter];
}

class ActivityLogInitial extends ActivityLogState {}

class ActivityLogLoading extends ActivityLogState {
  const ActivityLogLoading({super.activityLogs, super.currentFilter});

  @override
  List<Object?> get props => [activityLogs, currentFilter];
}

class ActivityLogLoaded extends ActivityLogState {
  final String? lastEvaluatedKey;
  final bool hasMore;

  const ActivityLogLoaded({
    required super.activityLogs,
    super.currentFilter,
    this.lastEvaluatedKey,
    this.hasMore = false,
  });

  @override
  List<Object?> get props => [
    activityLogs,
    currentFilter,
    lastEvaluatedKey,
    hasMore,
  ];
}

class ActivityLogLoadingMore extends ActivityLogLoaded {
  const ActivityLogLoadingMore({
    required super.activityLogs,
    super.currentFilter,
    super.lastEvaluatedKey,
    super.hasMore,
  });

  @override
  List<Object?> get props => [
    activityLogs,
    currentFilter,
    lastEvaluatedKey,
    hasMore,
  ];
}

class ActivityLogDetailsLoaded extends ActivityLogState {
  final ActivityLog currentActivityLog;

  const ActivityLogDetailsLoaded({
    required this.currentActivityLog,
    super.activityLogs,
    super.currentFilter,
  });

  @override
  List<Object> get props => [currentActivityLog, activityLogs, currentFilter];
}

class ActivityLogFailure extends ActivityLogState {
  final String message;

  const ActivityLogFailure({
    required this.message,
    super.activityLogs,
    super.currentFilter,
  });

  @override
  List<Object> get props => [message, activityLogs, currentFilter];
}
