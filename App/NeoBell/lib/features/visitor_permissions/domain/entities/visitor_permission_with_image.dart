import 'visitor_permission.dart';

class VisitorPermissionWithImage extends VisitorPermission {
  final String imageUrl;

  const VisitorPermissionWithImage({
    required super.faceTagId,
    required super.visitorName,
    required super.permissionLevel,
    required super.createdAt,
    required super.lastUpdatedAt,
    required this.imageUrl,
  });

  @override
  List<Object> get props => [...super.props, imageUrl];

  @override
  VisitorPermissionWithImage copyWith({
    String? faceTagId,
    String? visitorName,
    PermissionLevel? permissionLevel,
    DateTime? createdAt,
    DateTime? lastUpdatedAt,
    String? imageUrl,
  }) {
    return VisitorPermissionWithImage(
      faceTagId: faceTagId ?? this.faceTagId,
      visitorName: visitorName ?? this.visitorName,
      permissionLevel: permissionLevel ?? this.permissionLevel,
      createdAt: createdAt ?? this.createdAt,
      lastUpdatedAt: lastUpdatedAt ?? this.lastUpdatedAt,
      imageUrl: imageUrl ?? this.imageUrl,
    );
  }

  // Método para converter para VisitorPermission base (útil para operações que não precisam da imagem)
  VisitorPermission toVisitorPermission() {
    return VisitorPermission(
      faceTagId: faceTagId,
      visitorName: visitorName,
      permissionLevel: permissionLevel,
      createdAt: createdAt,
      lastUpdatedAt: lastUpdatedAt,
    );
  }
}
