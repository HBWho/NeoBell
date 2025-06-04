part of 'visitor_permission_bloc.dart';

@immutable
sealed class VisitorPermissionEvent {}

final class LoadVisitorPermissions extends VisitorPermissionEvent {
  final int? limit;
  final String? lastEvaluatedKey;

  LoadVisitorPermissions({this.limit, this.lastEvaluatedKey});
}

final class UpdateVisitorPermissionEvent extends VisitorPermissionEvent {
  final String faceTagId;
  final String visitorName;
  final PermissionLevel permissionLevel;

  UpdateVisitorPermissionEvent({
    required this.faceTagId,
    required this.visitorName,
    required this.permissionLevel,
  });
}

final class DeleteVisitorPermissionEvent extends VisitorPermissionEvent {
  final String faceTagId;

  DeleteVisitorPermissionEvent({required this.faceTagId});
}

final class LoadVisitorDetailsWithImage extends VisitorPermissionEvent {
  final String faceTagId;

  LoadVisitorDetailsWithImage({required this.faceTagId});
}

final class RefreshVisitorPermissions extends VisitorPermissionEvent {
  final bool clearCache;

  RefreshVisitorPermissions({this.clearCache = false});
}

final class RefreshVisitorDetailsWithImage extends VisitorPermissionEvent {
  final String faceTagId;

  RefreshVisitorDetailsWithImage({required this.faceTagId});
}
