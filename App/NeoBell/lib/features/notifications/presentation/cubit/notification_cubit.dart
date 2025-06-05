import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:fpdart/fpdart.dart';
import 'package:logger/logger.dart';
import 'package:neobell/core/usecase/usecase.dart';

import '../../../../init_dependencies_imports.dart';
import '../../../../routes.dart';
import '../../../package_deliveries/presentation/blocs/package_delivery_bloc.dart';
import '../../../package_deliveries/presentation/blocs/package_delivery_event.dart';
import '../../../video_messages/presentation/blocs/video_message_bloc.dart';
import '../../../video_messages/presentation/blocs/video_message_event.dart';
import '../../../visitor_permissions/presentation/blocs/visitor_permission_bloc.dart';
import '../../domain/entities/notification_channel.dart';
import '../../domain/entities/notification_message.dart';
import '../../domain/usecases/get_firebase_tolen.dart';
import '../../domain/usecases/initialize_notifications.dart';
import '../../domain/usecases/listen_to_notification_taps.dart';
import '../../domain/usecases/show_notification.dart';

part 'notification_state.dart';

class NotificationCubit extends Cubit<NotificationState> {
  NotificationCubit({
    required InitializeNotifications initializeNotifications,
    required ShowNotification showNotification,
    required GetFirebaseToken getFirebaseToken,
    required ListenToNotificationTaps listenToNotificationTaps,
  }) : _initializeNotifications = initializeNotifications,
       _showNotification = showNotification,
       _getFirebaseToken = getFirebaseToken,
       _listenToNotificationTaps = listenToNotificationTaps,
       super(NotificationInitial());

  final Logger _logger = Logger();
  final InitializeNotifications _initializeNotifications;
  final ShowNotification _showNotification;
  final GetFirebaseToken _getFirebaseToken;
  final ListenToNotificationTaps _listenToNotificationTaps;

  Map<NotificationChannel, bool> channelEnabledStates = {};

  Future<void> initialize() async {
    try {
      await _initializeNotifications(unit);
      final result = await _listenToNotificationTaps(NoParams());
      result.fold(
        (failure) => emit(NotificationError(failure.message)),
        (stream) => stream.listen(_handleNotificationTap),
      );
      emit(NotificationInitialized());
    } catch (e) {
      emit(NotificationError(e.toString()));
    }
  }

  Future<void> showNotification({
    required String title,
    required String body,
    required NotificationChannel channel,
    Map<String, dynamic>? payload,
  }) => _showNotification(
    NotificationMessage(
      title: title,
      body: body,
      channel: channel,
      payload: payload,
    ),
  );

  Future<String?> getFirebaseToken() async {
    try {
      final response = await _getFirebaseToken(unit);
      return response.fold((l) => null, (r) => r);
    } catch (e) {
      emit(NotificationError(e.toString()));
      return null;
    }
  }

  void _handleNotificationTap(Map<String, dynamic> data) {
    _logger.d(
      'NotificationRemoteDataSourceImpl: Handling notification tap with data: $data',
    );
    // Get the screen target
    final String? screenTarget = data['screen_target'] as String?;

    if (screenTarget == null) {
      _logger.w(
        'NotificationRemoteDataSourceImpl: No screen target in notification data. Navigating to home.',
      );
      return;
    }
    try {
      switch (screenTarget) {
        case 'watch-video':
          _logger.i(
            'NotificationRemoteDataSourceImpl: Navigating to watch-video.',
          );
          final String? messageId = data['message_id'] as String?;
          if (messageId == null || messageId.isEmpty) {
            _logger.w(
              'NotificationRemoteDataSourceImpl: No videoId provided for watch-video.',
            );
            return;
          }
          serviceLocator<VideoMessageBloc>().add(
            GenerateViewUrlEvent(messageId),
          );
          RouterMain.router.goNamed('home');
          RouterMain.router.pushNamed(
            'watch-video',
            pathParameters: {'id': messageId},
          );
          break;
        case 'package-delivery-details':
          _logger.i(
            'NotificationRemoteDataSourceImpl: Navigating to package-delivery-details.',
          );
          final String? orderId = data['order_id'] as String?;
          if (orderId == null || orderId.isEmpty) {
            _logger.w(
              'NotificationRemoteDataSourceImpl: No orderId provided for package-delivery-details.',
            );
            return;
          }
          serviceLocator<PackageDeliveryBloc>().add(
            LoadPackageDeliveryDetails(orderId),
          );
          RouterMain.router.goNamed('home');
          RouterMain.router.pushNamed(
            '/package-delivery-details',
            pathParameters: {'orderId': orderId},
          );
          break;
        case 'visitor-permission-details':
          _logger.i(
            'NotificationRemoteDataSourceImpl: Navigating to visitor-permission-details.',
          );
          final String? faceTagId = data['face_tag_id'] as String?;
          if (faceTagId == null || faceTagId.isEmpty) {
            _logger.w(
              'NotificationRemoteDataSourceImpl: No faceTagId provided for visitor-permission-details.',
            );
            return;
          }
          serviceLocator<VisitorPermissionBloc>().add(
            LoadVisitorDetailsWithImage(faceTagId: faceTagId),
          );
          RouterMain.router.goNamed('home');
          RouterMain.router.pushNamed(
            'visitor-permission-details',
            pathParameters: {'id': faceTagId},
          );
          break;
        default:
          break;
      }
    } catch (e, s) {
      _logger.e(
        'NotificationRemoteDataSourceImpl: Error during navigation from notification tap.',
        error: e,
        stackTrace: s,
      );
    }
  }
}
