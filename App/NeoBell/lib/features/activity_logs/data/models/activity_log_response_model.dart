import '../../domain/entities/activity_log_response.dart';
import 'activity_log_model.dart';

class ActivityLogResponseModel extends ActivityLogResponse {
  const ActivityLogResponseModel({
    required super.items,
    super.lastEvaluatedKey,
    super.hasMore,
  });

  factory ActivityLogResponseModel.fromJson(Map<String, dynamic> json) {
    final itemsList = json['items'] as List<dynamic>? ?? [];
    final items =
        itemsList
            .map(
              (item) => ActivityLogModel.fromJson(item as Map<String, dynamic>),
            )
            .toList();

    final lastEvaluatedKey = json['last_evaluated_key'] as String?;

    return ActivityLogResponseModel(
      items: items,
      lastEvaluatedKey: lastEvaluatedKey,
      hasMore: lastEvaluatedKey != null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'items':
          items
              .map((item) => ActivityLogModel.fromEntity(item).toJson())
              .toList(),
      if (lastEvaluatedKey != null) 'last_evaluated_key': lastEvaluatedKey,
    };
  }

  factory ActivityLogResponseModel.fromEntity(ActivityLogResponse entity) {
    return ActivityLogResponseModel(
      items: entity.items,
      lastEvaluatedKey: entity.lastEvaluatedKey,
      hasMore: entity.hasMore,
    );
  }
}
