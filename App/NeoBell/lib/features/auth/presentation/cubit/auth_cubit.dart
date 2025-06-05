import 'dart:async';

import 'package:amplify_flutter/amplify_flutter.dart' hide AuthUser;
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:equatable/equatable.dart';
import 'package:logger/web.dart';

import '../../../../core/services/token_manager.dart';
import '../../../../core/usecase/usecase.dart';
import '../../../notifications/presentation/cubit/notification_cubit.dart';
import '../../domain/entities/auth_user.dart';
import '../../domain/usecases/check_auth_status.dart';
import '../../domain/usecases/sign_in.dart';
import '../../domain/usecases/sign_out.dart';
import '../../domain/usecases/update_password.dart';
import '../../../user_profile/presentation/cubit/user_profile_cubit.dart';

part 'auth_state.dart';

class AuthCubit extends Cubit<AuthState> {
  final Logger _logger = Logger();
  final SignIn _signIn;
  final SignOut _signOut;
  final CheckAuthStatus _checkAuthStatus;
  final UpdatePassword _updatePassword;
  final TokenManager _tokenManager;
  final UserProfileCubit _userProfileCubit;
  final NotificationCubit _notificationCubit;

  StreamSubscription? _hubSubscription;

  AuthCubit({
    required SignIn signIn,
    required SignOut signOut,
    required CheckAuthStatus checkAuthStatus,
    required UpdatePassword updatePassword,
    required TokenManager tokenManager,
    required UserProfileCubit userProfileCubit,
    required NotificationCubit notificationCubit,
  }) : _signIn = signIn,
       _signOut = signOut,
       _checkAuthStatus = checkAuthStatus,
       _updatePassword = updatePassword,
       _tokenManager = tokenManager,
       _userProfileCubit = userProfileCubit,
       _notificationCubit = notificationCubit,
       super(AuthInitial()) {
    _listenToAuthEvents();
  }

  void _listenToAuthEvents() {
    _hubSubscription = Amplify.Hub.listen(HubChannel.Auth, (HubEvent hubEvent) {
      _logger.i('Amplify Hub: Auth event - ${hubEvent.eventName}');
      switch (hubEvent.eventName) {
        case 'SIGNED_IN':
        case 'SIGNED_OUT':
          checkAuthStatus();
          break;
        case 'SESSION_EXPIRED':
          sessionExpired();
          break;
        case 'USER_DELETED':
          _tokenManager.clearToken();
          emit(AuthUnauthenticated());
          break;
        default:
          break;
      }
    });
  }

  @override
  Future<void> close() {
    _hubSubscription?.cancel();
    return super.close();
  }

  Future<void> checkAuthStatus() async {
    emit(AuthInProgress());
    final result = await _checkAuthStatus(NoParams());
    result.fold((failure) => emit(AuthError(failure.message)), (user) {
      if (user != null) {
        emit(AuthAuthenticated(user));
        _updateFcmToken(); // Update FCM token if available
      } else {
        emit(AuthUnauthenticated());
      }
    });
  }

  Future<void> signIn({
    required String username,
    required String password,
  }) async {
    emit(AuthInProgress());
    final result = await _signIn(
      SignInParams(username: username, password: password),
    );
    result.fold((failure) => emit(AuthError(failure.message)), (user) {
      emit(AuthAuthenticated(user));
      _updateFcmToken(); // Update FCM token after successful login
    });
  }

  Future<void> signOut() async {
    emit(AuthInProgress());
    final result = await _signOut(NoParams());
    result.fold((failure) => emit(AuthError(failure.message)), (_) {
      _tokenManager.clearToken();
      emit(AuthUnauthenticated());
    });
  }

  void sessionExpired() {
    emit(AuthSessionExpired());
  }

  Future<void> updatePassword({
    required String oldPassword,
    required String newPassword,
  }) async {
    emit(AuthInProgress());
    final result = await _updatePassword(
      UpdatePasswordParams(oldPassword: oldPassword, newPassword: newPassword),
    );
    result.fold((failure) => emit(AuthError(failure.message)), (_) {
      // Voltar ao estado autenticado após sucesso
      if (state is AuthInProgress) {
        checkAuthStatus();
      }
    });
  }

  // Private method to handle FCM token update
  Future<void> _updateFcmToken() async {
    try {
      final token = await _notificationCubit.getFirebaseToken();
      if (token != null) {
        await _userProfileCubit.updateDeviceToken(token);
      }
    } catch (e) {
      _logger.e('Failed to update FCM token: $e');
    }
  }
}
