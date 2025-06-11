part of 'auth_cubit.dart';

/// Base class for all authentication states
abstract class AuthState extends Equatable {
  const AuthState();

  @override
  List<Object?> get props => [];
}

/// Initial state when the app starts
class AuthInitial extends AuthState {}

/// User is authenticated and can access protected resources
class AuthAuthenticated extends AuthState {
  final AuthUser user;

  const AuthAuthenticated(this.user);

  @override
  List<Object> get props => [user];
}

/// User is not authenticated
class AuthUnauthenticated extends AuthState {}

/// Session expired, requires re-authentication
class AuthSessionExpired extends AuthState {}

/// Authentication is in progress
class AuthInProgress extends AuthState {}

/// Authentication error occurred
class AuthError extends AuthState {
  final String message;

  const AuthError(this.message);

  @override
  List<Object> get props => [message];
}

/// User is authenticated but needs biometric verification
class AuthRequiresBiometric extends AuthState {
  final AuthUser user;

  const AuthRequiresBiometric(this.user);

  @override
  List<Object> get props => [user];
}

/// Biometric authentication is in progress
class AuthBiometricInProgress extends AuthState {
  final AuthUser user;

  const AuthBiometricInProgress(this.user);

  @override
  List<Object> get props => [user];
}
