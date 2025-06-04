import 'package:equatable/equatable.dart';
import 'activity_log.dart';

class ActivityLogResponse extends Equatable {
  final List<ActivityLog> items;
  final String? lastEvaluatedKey;
  final bool hasMore;

  const ActivityLogResponse({
    required this.items,
    this.lastEvaluatedKey,
    this.hasMore = false,
  });

  @override
  List<Object?> get props => [items, lastEvaluatedKey, hasMore];

  ActivityLogResponse copyWith({
    List<ActivityLog>? items,
    String? lastEvaluatedKey,
    bool? hasMore,
  }) {
    return ActivityLogResponse(
      items: items ?? this.items,
      lastEvaluatedKey: lastEvaluatedKey ?? this.lastEvaluatedKey,
      hasMore: hasMore ?? this.hasMore,
    );
  }
}
