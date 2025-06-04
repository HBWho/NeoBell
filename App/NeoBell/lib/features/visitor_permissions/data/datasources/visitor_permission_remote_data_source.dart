import '../../../../core/constants/api_constants.dart';
import '../../../../core/data/api_service.dart';
import '../../../../core/error/server_exception.dart';
import '../models/visitor_permission_model.dart';
import '../models/visitor_permission_with_image_model.dart';

abstract interface class VisitorPermissionRemoteDataSource {
  Future<List<VisitorPermissionModel>> getVisitorPermissions({
    int? limit,
    String? lastEvaluatedKey,
  });

  Future<VisitorPermissionWithImageModel> getVisitorDetailsWithImage(
    String faceTagId,
  );

  Future<void> updateVisitorPermission({
    required String faceTagId,
    required String visitorName,
    required String permissionLevel,
  });

  Future<void> deleteVisitorPermission(String faceTagId);
}

class VisitorPermissionRemoteDataSourceImpl
    implements VisitorPermissionRemoteDataSource {
  final ApiService apiService;

  VisitorPermissionRemoteDataSourceImpl({required this.apiService});

  @override
  Future<List<VisitorPermissionModel>> getVisitorPermissions({
    int? limit,
    String? lastEvaluatedKey,
  }) async {
    try {
      final queryParams = <String, String>{};
      if (limit != null) {
        queryParams['limit'] = limit.toString();
      }
      if (lastEvaluatedKey != null) {
        queryParams['last_evaluated_key'] = lastEvaluatedKey;
      }

      final response = await apiService.getData(
        endPoint: ApiEndpoints.getVisitorPermissions,
        queryParams: queryParams.isNotEmpty ? queryParams : null,
      );

      final List<dynamic> items = response['items'] ?? [];
      return items
          .map(
            (item) =>
                VisitorPermissionModel.fromJson(item as Map<String, dynamic>),
          )
          .toList();
    } on ServerException {
      rethrow;
    } catch (e) {
      throw ServerException('Failed to fetch visitor permissions: $e');
    }
  }

  @override
  Future<VisitorPermissionWithImageModel> getVisitorDetailsWithImage(
    String faceTagId,
  ) async {
    try {
      final response = await apiService.postData(
        endPoint: ApiEndpoints.generateVisitorImageUrl,
        pathParams: {'face_tag_id': faceTagId},
      );

      return VisitorPermissionWithImageModel.fromJson(response);
    } on ServerException {
      rethrow;
    } catch (e) {
      throw ServerException('Failed to fetch visitor details with image: $e');
    }
  }

  @override
  Future<void> updateVisitorPermission({
    required String faceTagId,
    required String visitorName,
    required String permissionLevel,
  }) async {
    try {
      await apiService.updateData(
        endPoint: ApiEndpoints.updateVisitorPermission,
        pathParams: {'face_tag_id': faceTagId},
        body: {
          'visitor_name': visitorName,
          'permission_level': permissionLevel,
        },
      );
    } on ServerException {
      rethrow;
    } catch (e) {
      throw ServerException('Failed to update visitor permission: $e');
    }
  }

  @override
  Future<void> deleteVisitorPermission(String faceTagId) async {
    try {
      await apiService.deleteData(
        endPoint: ApiEndpoints.deleteVisitorPermission,
        pathParams: {'face_tag_id': faceTagId},
      );
    } on ServerException {
      rethrow;
    } catch (e) {
      throw ServerException('Failed to delete visitor permission: $e');
    }
  }
}
