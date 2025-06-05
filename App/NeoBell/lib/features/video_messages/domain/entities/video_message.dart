import 'package:equatable/equatable.dart';

class VideoMessage extends Equatable {
  final String messageId;
  final String sbcId;
  final String visitorId;
  final String? visitorName;
  final String deviceFriendlyName;
  final DateTime recordedAt;
  final int durationSec;
  final bool isViewed;

  const VideoMessage({
    required this.messageId,
    required this.sbcId,
    required this.visitorId,
    this.visitorName,
    required this.deviceFriendlyName,
    required this.recordedAt,
    required this.durationSec,
    this.isViewed = false,
  });

  @override
  List<Object?> get props => [
    messageId,
    sbcId,
    deviceFriendlyName,
    recordedAt,
    durationSec,
    visitorName,
    visitorId,
    isViewed,
  ];

  VideoMessage copyWith({
    String? messageId,
    String? sbcId,
    String? deviceFriendlyName,
    DateTime? recordedAt,
    int? durationSec,
    String? visitorName,
    String? visitorId,
    bool? isViewed,
  }) {
    return VideoMessage(
      messageId: messageId ?? this.messageId,
      sbcId: sbcId ?? this.sbcId,
      deviceFriendlyName: deviceFriendlyName ?? this.deviceFriendlyName,
      recordedAt: recordedAt ?? this.recordedAt,
      durationSec: durationSec ?? this.durationSec,
      visitorName: visitorName ?? this.visitorName,
      visitorId: visitorId ?? this.visitorId,
      isViewed: isViewed ?? this.isViewed,
    );
  }
}
