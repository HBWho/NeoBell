import '../../domain/entities/video_message.dart';

class VideoMessageModel extends VideoMessage {
  const VideoMessageModel({
    required super.messageId,
    required super.sbcId,

    required super.deviceFriendlyName,
    required super.recordedAt,
    required super.durationSec,
    required super.visitorName,
    required super.visitorId,
    super.isViewed,
  });

  factory VideoMessageModel.fromJson(Map<String, dynamic> json) {
    return VideoMessageModel(
      messageId: json['message_id'],
      sbcId: json['sbc_id'],
      deviceFriendlyName: json['device_friendly_name'] ?? '',
      recordedAt: DateTime.parse(json['recorded_at']),
      durationSec: json['duration_sec'] ?? 0,
      visitorName: json['visitor_name'],
      visitorId: json['visitor_face_tag_id'],
      isViewed:
          json['is_viewed'] is bool
              ? json['is_viewed']
              : json['is_viewed'] is String
              ? json['is_viewed'] == 'true'
              : false,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'message_id': messageId,
      'sbc_id': sbcId,
      'device_friendly_name': deviceFriendlyName,
      'recorded_at': recordedAt.toIso8601String(),
      'duration_sec': durationSec,
      'visitor_name': visitorName,
      'visitor_face_tag_id': visitorId,
      'is_viewed': isViewed,
    };
  }

  factory VideoMessageModel.fromEntity(VideoMessage entity) {
    return VideoMessageModel(
      messageId: entity.messageId,
      sbcId: entity.sbcId,
      deviceFriendlyName: entity.deviceFriendlyName,
      recordedAt: entity.recordedAt,
      durationSec: entity.durationSec,
      visitorName: entity.visitorName,
      visitorId: entity.visitorId,
      isViewed: entity.isViewed,
    );
  }
}
