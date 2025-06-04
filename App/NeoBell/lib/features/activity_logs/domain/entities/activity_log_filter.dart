import 'package:equatable/equatable.dart';

class ActivityLogFilter extends Equatable {
  final List<String>? eventTypes;
  final String? sbcId;
  final DateTime? startDate;
  final DateTime? endDate;
  final int? limit;
  final String? lastEvaluatedKey;

  const ActivityLogFilter({
    this.eventTypes,
    this.sbcId,
    this.startDate,
    this.endDate,
    this.limit,
    this.lastEvaluatedKey,
  });

  @override
  List<Object?> get props => [
    eventTypes,
    sbcId,
    startDate,
    endDate,
    limit,
    lastEvaluatedKey,
  ];

  ActivityLogFilter copyWith({
    List<String>? eventTypes,
    String? sbcId,
    DateTime? startDate,
    DateTime? endDate,
    int? limit,
    String? lastEvaluatedKey,
  }) {
    return ActivityLogFilter(
      eventTypes: eventTypes ?? this.eventTypes,
      sbcId: sbcId ?? this.sbcId,
      startDate: startDate ?? this.startDate,
      endDate: endDate ?? this.endDate,
      limit: limit ?? this.limit,
      lastEvaluatedKey: lastEvaluatedKey ?? this.lastEvaluatedKey,
    );
  }

  Map<String, dynamic> toQueryParameters() {
    final Map<String, dynamic> params = {};

    if (eventTypes != null && eventTypes!.isNotEmpty) {
      params['event_types'] = eventTypes!.join(',');
    }
    if (sbcId != null) {
      params['sbc_id'] = sbcId;
    }
    if (startDate != null) {
      params['start_date'] = startDate!.toIso8601String();
    }
    if (endDate != null) {
      params['end_date'] = endDate!.toIso8601String();
    }
    if (limit != null) {
      params['limit'] = limit.toString();
    }
    if (lastEvaluatedKey != null) {
      params['last_evaluated_key'] = lastEvaluatedKey;
    }

    return params;
  }
}
