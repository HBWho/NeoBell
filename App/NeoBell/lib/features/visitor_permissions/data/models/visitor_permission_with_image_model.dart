import '../../domain/entities/visitor_permission.dart';
import '../../domain/entities/visitor_permission_with_image.dart';

class VisitorPermissionWithImageModel extends VisitorPermissionWithImage {
  const VisitorPermissionWithImageModel({
    required super.faceTagId,
    required super.visitorName,
    required super.permissionLevel,
    required super.createdAt,
    required super.lastUpdatedAt,
    required super.imageUrl,
  });

  factory VisitorPermissionWithImageModel.fromJson(Map<String, dynamic> json) {
    return VisitorPermissionWithImageModel(
      faceTagId: json['face_tag_id'] as String,
      visitorName: json['visitor_name'] as String,
      permissionLevel: PermissionLevel.fromString(
        json['permission_level'] as String,
      ),
      createdAt: DateTime.parse(json['created_at'] as String),
      lastUpdatedAt: DateTime.parse(json['last_updated_at'] as String),
      imageUrl: json['image_url'] as String,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'face_tag_id': faceTagId,
      'visitor_name': visitorName,
      'permission_level': permissionLevel.value,
      'created_at': createdAt.toIso8601String(),
      'last_updated_at': lastUpdatedAt.toIso8601String(),
      'image_url': imageUrl,
    };
  }

  factory VisitorPermissionWithImageModel.fromEntity(
    VisitorPermissionWithImage entity,
  ) {
    return VisitorPermissionWithImageModel(
      faceTagId: entity.faceTagId,
      visitorName: entity.visitorName,
      permissionLevel: entity.permissionLevel,
      createdAt: entity.createdAt,
      lastUpdatedAt: entity.lastUpdatedAt,
      imageUrl: entity.imageUrl,
    );
  }
}
