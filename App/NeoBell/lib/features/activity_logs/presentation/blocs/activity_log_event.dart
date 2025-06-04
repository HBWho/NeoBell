part of 'activity_log_bloc.dart';

@immutable
sealed class ActivityLogEvent {}

final class LoadActivityLogs extends ActivityLogEvent {
  final ActivityLogFilter filter;

  LoadActivityLogs({required this.filter});
}

final class LoadMoreActivityLogs extends ActivityLogEvent {}

final class SelectActivityLogFromCache extends ActivityLogEvent {
  final String logSourceId;
  final String timestampUuid;

  SelectActivityLogFromCache({
    required this.logSourceId,
    required this.timestampUuid,
  });
}

final class RefreshActivityLogs extends ActivityLogEvent {}

final class ApplyActivityLogFilter extends ActivityLogEvent {
  final ActivityLogFilter filter;

  ApplyActivityLogFilter({required this.filter});
}
