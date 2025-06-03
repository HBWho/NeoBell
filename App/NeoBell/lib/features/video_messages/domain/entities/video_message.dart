import 'package:equatable/equatable.dart';

class VideoMessage extends Equatable {
  final String messageId;
  final String sbcId;
  final String deviceFriendlyName;
  final DateTime recordedAt;
  final int durationSec;
  final String? visitorNameIfKnown;
  final bool isViewed;

  const VideoMessage({
    required this.messageId,
    required this.sbcId,
    required this.deviceFriendlyName,
    required this.recordedAt,
    required this.durationSec,
    this.visitorNameIfKnown,
    this.isViewed = false,
  });

  @override
  List<Object?> get props => [
        messageId,
        sbcId,
        deviceFriendlyName,
        recordedAt,
        durationSec,
        visitorNameIfKnown,
        isViewed,
      ];

  VideoMessage copyWith({
    String? messageId,
    String? sbcId,
    String? deviceFriendlyName,
    DateTime? recordedAt,
    int? durationSec,
    String? visitorNameIfKnown,
    bool? isViewed,
  }) {
    return VideoMessage(
      messageId: messageId ?? this.messageId,
      sbcId: sbcId ?? this.sbcId,
      deviceFriendlyName: deviceFriendlyName ?? this.deviceFriendlyName,
      recordedAt: recordedAt ?? this.recordedAt,
      durationSec: durationSec ?? this.durationSec,
      visitorNameIfKnown: visitorNameIfKnown ?? this.visitorNameIfKnown,
      isViewed: isViewed ?? this.isViewed,
    );
  }
}
