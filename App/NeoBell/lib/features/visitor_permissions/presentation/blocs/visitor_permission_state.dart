part of 'visitor_permission_bloc.dart';

abstract class VisitorPermissionState extends Equatable {
  final List<VisitorPermission> visitorPermissions;
  final List<VisitorPermissionWithImage> cachedVisitorDetails;

  const VisitorPermissionState({
    this.visitorPermissions = const [],
    this.cachedVisitorDetails = const [],
  });

  @override
  List<Object?> get props => [visitorPermissions, cachedVisitorDetails];
}

class VisitorPermissionInitial extends VisitorPermissionState {}

class VisitorPermissionLoading extends VisitorPermissionState {
  const VisitorPermissionLoading({
    super.visitorPermissions,
    super.cachedVisitorDetails,
  });

  @override
  List<Object?> get props => [visitorPermissions, cachedVisitorDetails];
}

class VisitorPermissionLoaded extends VisitorPermissionState {
  final String? lastEvaluatedKey;

  const VisitorPermissionLoaded({
    required super.visitorPermissions,
    super.cachedVisitorDetails,
    this.lastEvaluatedKey,
  });

  @override
  List<Object?> get props => [
    visitorPermissions,
    cachedVisitorDetails,
    lastEvaluatedKey,
  ];
}

class VisitorPermissionDetailsLoaded extends VisitorPermissionState {
  final VisitorPermissionWithImage currentVisitorDetails;

  const VisitorPermissionDetailsLoaded({
    required this.currentVisitorDetails,
    super.visitorPermissions,
    super.cachedVisitorDetails,
  });

  @override
  List<Object> get props => [
    currentVisitorDetails,
    visitorPermissions,
    cachedVisitorDetails,
  ];
}

class VisitorPermissionOperationSuccess extends VisitorPermissionState {
  final String message;

  const VisitorPermissionOperationSuccess({
    required this.message,
    super.visitorPermissions,
    super.cachedVisitorDetails,
  });

  @override
  List<Object> get props => [message, visitorPermissions, cachedVisitorDetails];
}

class VisitorPermissionFailure extends VisitorPermissionState {
  final String message;

  const VisitorPermissionFailure({
    required this.message,
    super.visitorPermissions,
    super.cachedVisitorDetails,
  });

  @override
  List<Object> get props => [message, visitorPermissions, cachedVisitorDetails];
}
