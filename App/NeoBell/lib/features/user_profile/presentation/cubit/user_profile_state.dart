part of 'user_profile_cubit.dart';

abstract class UserProfileState extends Equatable {
  const UserProfileState();

  @override
  List<Object?> get props => [];
}

class UserProfileInitial extends UserProfileState {
  const UserProfileInitial();
}

class UserProfileLoading extends UserProfileState {
  const UserProfileLoading();
}

class UserProfileLoaded extends UserProfileState {
  final UserProfile profile;
  final String? message;

  const UserProfileLoaded(this.profile, {this.message});

  @override
  List<Object?> get props => [profile, message];

  UserProfileLoaded copyWith({UserProfile? profile, String? message}) {
    return UserProfileLoaded(profile ?? this.profile, message: message);
  }
}

class UserProfileError extends UserProfileState {
  final String message;
  const UserProfileError(this.message);

  @override
  List<Object?> get props => [message];
}
