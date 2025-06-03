import 'package:equatable/equatable.dart';

/// Represents the authenticated user's core data from Cognito
class AuthUser extends Equatable {
  final String id;
  final String email;
  final String? name;
  final bool isEmailVerified;
  final DateTime? lastSignInAt;

  const AuthUser({
    required this.id,
    required this.email,
    this.name,
    required this.isEmailVerified,
    this.lastSignInAt,
  });

  @override
  List<Object?> get props => [id, email, name, isEmailVerified, lastSignInAt];
}
