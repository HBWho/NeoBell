import '../../domain/entities/activity_log.dart';

class ActivityLogModel extends ActivityLog {
  const ActivityLogModel({
    required super.logSourceId,
    required super.timestampUuid,
    required super.eventType,
    required super.timestamp,
    required super.summary,
    super.sbcIdRelated,
    super.userIdRelated,
    super.details,
  });

  factory ActivityLogModel.fromJson(Map<String, dynamic> json) {
    return ActivityLogModel(
      logSourceId: json['log_source_id'] ?? '',
      timestampUuid: json['timestamp_uuid'] ?? '',
      eventType: json['event_type'] ?? '',
      timestamp: DateTime.parse(
        json['timestamp'] ?? DateTime.now().toIso8601String(),
      ),
      summary: json['summary'] ?? '',
      sbcIdRelated: json['sbc_id_related'],
      userIdRelated: json['user_id_related'],
      details:
          json['details'] != null
              ? Map<String, dynamic>.from(json['details'])
              : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'log_source_id': logSourceId,
      'timestamp_uuid': timestampUuid,
      'event_type': eventType,
      'timestamp': timestamp.toIso8601String(),
      'summary': summary,
      if (sbcIdRelated != null) 'sbc_id_related': sbcIdRelated,
      if (userIdRelated != null) 'user_id_related': userIdRelated,
      if (details != null) 'details': details,
    };
  }

  factory ActivityLogModel.fromEntity(ActivityLog entity) {
    return ActivityLogModel(
      logSourceId: entity.logSourceId,
      timestampUuid: entity.timestampUuid,
      eventType: entity.eventType,
      timestamp: entity.timestamp,
      summary: entity.summary,
      sbcIdRelated: entity.sbcIdRelated,
      userIdRelated: entity.userIdRelated,
      details: entity.details,
    );
  }
}
