import 'package:equatable/equatable.dart';

class ActivityLog extends Equatable {
  final String logSourceId;
  final String timestampUuid;
  final String eventType;
  final DateTime timestamp;
  final String summary;
  final String? sbcIdRelated;
  final String? userIdRelated;
  final Map<String, dynamic>? details;

  const ActivityLog({
    required this.logSourceId,
    required this.timestampUuid,
    required this.eventType,
    required this.timestamp,
    required this.summary,
    this.sbcIdRelated,
    this.userIdRelated,
    this.details,
  });

  @override
  List<Object?> get props => [
    logSourceId,
    timestampUuid,
    eventType,
    timestamp,
    summary,
    sbcIdRelated,
    userIdRelated,
    details,
  ];

  ActivityLog copyWith({
    String? logSourceId,
    String? timestampUuid,
    String? eventType,
    DateTime? timestamp,
    String? summary,
    String? sbcIdRelated,
    String? userIdRelated,
    Map<String, dynamic>? details,
  }) {
    return ActivityLog(
      logSourceId: logSourceId ?? this.logSourceId,
      timestampUuid: timestampUuid ?? this.timestampUuid,
      eventType: eventType ?? this.eventType,
      timestamp: timestamp ?? this.timestamp,
      summary: summary ?? this.summary,
      sbcIdRelated: sbcIdRelated ?? this.sbcIdRelated,
      userIdRelated: userIdRelated ?? this.userIdRelated,
      details: details ?? this.details,
    );
  }
}
