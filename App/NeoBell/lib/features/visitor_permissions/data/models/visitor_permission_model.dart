import '../../domain/entities/visitor_permission.dart';

class VisitorPermissionModel extends VisitorPermission {
  const VisitorPermissionModel({
    required super.faceTagId,
    required super.visitorName,
    required super.permissionLevel,
    required super.createdAt,
    required super.lastUpdatedAt,
  });

  factory VisitorPermissionModel.fromJson(Map<String, dynamic> json) {
    return VisitorPermissionModel(
      faceTagId: json['face_tag_id'] as String,
      visitorName: json['visitor_name'] as String,
      permissionLevel: PermissionLevel.fromString(
        json['permission_level'] as String,
      ),
      createdAt: DateTime.parse(json['created_at'] as String),
      lastUpdatedAt: DateTime.parse(json['last_updated_at'] as String),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'face_tag_id': faceTagId,
      'visitor_name': visitorName,
      'permission_level': permissionLevel.value,
      'created_at': createdAt.toIso8601String(),
      'last_updated_at': lastUpdatedAt.toIso8601String(),
    };
  }

  factory VisitorPermissionModel.fromEntity(VisitorPermission entity) {
    return VisitorPermissionModel(
      faceTagId: entity.faceTagId,
      visitorName: entity.visitorName,
      permissionLevel: entity.permissionLevel,
      createdAt: entity.createdAt,
      lastUpdatedAt: entity.lastUpdatedAt,
    );
  }
}
