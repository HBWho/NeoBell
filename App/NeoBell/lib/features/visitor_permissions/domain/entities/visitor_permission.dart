import 'package:equatable/equatable.dart';

class VisitorPermission extends Equatable {
  final String faceTagId;
  final String visitorName;
  final PermissionLevel permissionLevel;
  final DateTime createdAt;
  final DateTime lastUpdatedAt;

  const VisitorPermission({
    required this.faceTagId,
    required this.visitorName,
    required this.permissionLevel,
    required this.createdAt,
    required this.lastUpdatedAt,
  });

  @override
  List<Object> get props => [
    faceTagId,
    visitorName,
    permissionLevel,
    createdAt,
    lastUpdatedAt,
  ];

  VisitorPermission copyWith({
    String? faceTagId,
    String? visitorName,
    PermissionLevel? permissionLevel,
    DateTime? createdAt,
    DateTime? lastUpdatedAt,
  }) {
    return VisitorPermission(
      faceTagId: faceTagId ?? this.faceTagId,
      visitorName: visitorName ?? this.visitorName,
      permissionLevel: permissionLevel ?? this.permissionLevel,
      createdAt: createdAt ?? this.createdAt,
      lastUpdatedAt: lastUpdatedAt ?? this.lastUpdatedAt,
    );
  }
}

enum PermissionLevel {
  allowed('Allowed'),
  denied('Denied');

  const PermissionLevel(this.value);
  final String value;

  static PermissionLevel fromString(String value) {
    switch (value) {
      case 'Allowed':
        return PermissionLevel.allowed;
      case 'Denied':
        return PermissionLevel.denied;
      default:
        throw ArgumentError('Invalid permission level: $value');
    }
  }
}
