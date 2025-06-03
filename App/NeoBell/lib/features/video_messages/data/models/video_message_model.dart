import '../../domain/entities/video_message.dart';

class VideoMessageModel extends VideoMessage {
  const VideoMessageModel({
    required String messageId,
    required String sbcId,
    required String deviceFriendlyName,
    required DateTime recordedAt,
    required int durationSec,
    String? visitorNameIfKnown,
    bool isViewed = false,
  }) : super(
          messageId: messageId,
          sbcId: sbcId,
          deviceFriendlyName: deviceFriendlyName,
          recordedAt: recordedAt,
          durationSec: durationSec,
          visitorNameIfKnown: visitorNameIfKnown,
          isViewed: isViewed,
        );

  factory VideoMessageModel.fromJson(Map<String, dynamic> json) {
    return VideoMessageModel(
      messageId: json['message_id'],
      sbcId: json['sbc_id'],
      deviceFriendlyName: json['device_friendly_name'],
      recordedAt: DateTime.parse(json['recorded_at']),
      durationSec: json['duration_sec'],
      visitorNameIfKnown: json['visitor_name_if_known'],
      isViewed: json['is_viewed'] ?? false,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'message_id': messageId,
      'sbc_id': sbcId,
      'device_friendly_name': deviceFriendlyName,
      'recorded_at': recordedAt.toIso8601String(),
      'duration_sec': durationSec,
      'visitor_name_if_known': visitorNameIfKnown,
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
      visitorNameIfKnown: entity.visitorNameIfKnown,
      isViewed: entity.isViewed,
    );
  }
}
