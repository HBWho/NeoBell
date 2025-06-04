import '../../../../core/constants/api_constants.dart';
import '../../../../core/data/api_service.dart';
import '../../../../core/error/server_exception.dart';
import '../../domain/entities/create_package_delivery.dart';
import '../../domain/entities/package_delivery_filter.dart';
import '../../domain/entities/update_package_delivery.dart';
import '../models/package_delivery_model.dart';

abstract interface class PackageDeliveryRemoteDataSource {
  Future<List<PackageDeliveryModel>> getPackageDeliveries({
    PackageDeliveryFilter? filter,
    int? limit,
    String? lastEvaluatedKey,
  });

  Future<PackageDeliveryModel> getPackageDeliveryById(String orderId);

  Future<PackageDeliveryModel> createPackageDelivery(
    CreatePackageDelivery delivery,
  );

  Future<PackageDeliveryModel> updatePackageDelivery(
    String orderId,
    UpdatePackageDelivery delivery,
  );

  Future<void> deletePackageDelivery(String orderId);
}

class PackageDeliveryRemoteDataSourceImpl
    implements PackageDeliveryRemoteDataSource {
  final ApiService _apiService;

  PackageDeliveryRemoteDataSourceImpl(this._apiService);

  @override
  Future<List<PackageDeliveryModel>> getPackageDeliveries({
    PackageDeliveryFilter? filter,
    int? limit,
    String? lastEvaluatedKey,
  }) async {
    try {
      final Map<String, String> queryParams = {};

      if (filter != null) {
        final filterParams = filter.toQueryParameters();
        filterParams.forEach((key, value) {
          queryParams[key] = value.toString();
        });
      }

      if (limit != null) queryParams['limit'] = limit.toString();
      if (lastEvaluatedKey != null)
        queryParams['last_evaluated_key'] = lastEvaluatedKey;

      final response = await _apiService.getData(
        endPoint: ApiEndpoints.getDeliveries,
        queryParams: queryParams.isNotEmpty ? queryParams : null,
      );

      final List<dynamic> deliveriesJson = response['items'] ?? [];
      return deliveriesJson
          .map((json) => PackageDeliveryModel.fromJson(json))
          .toList();
    } catch (e) {
      throw ServerException('Failed to get package deliveries: $e');
    }
  }

  @override
  Future<PackageDeliveryModel> getPackageDeliveryById(String orderId) async {
    try {
      final response = await _apiService.getData(
        endPoint: ApiEndpoints.getDeliveryDetails,
        pathParams: {'order_id': orderId},
      );
      return PackageDeliveryModel.fromJson(response);
    } catch (e) {
      throw ServerException('Failed to get package delivery: $e');
    }
  }

  @override
  Future<PackageDeliveryModel> createPackageDelivery(
    CreatePackageDelivery delivery,
  ) async {
    try {
      final response = await _apiService.postData(
        endPoint: ApiEndpoints.createDelivery,
        body: delivery.toJson(),
      );
      return PackageDeliveryModel.fromJson(response);
    } catch (e) {
      throw ServerException('Failed to create package delivery: $e');
    }
  }

  @override
  Future<PackageDeliveryModel> updatePackageDelivery(
    String orderId,
    UpdatePackageDelivery delivery,
  ) async {
    try {
      await _apiService.updateData(
        endPoint: ApiEndpoints.updateDelivery,
        pathParams: {'order_id': orderId},
        body: delivery.toJson(),
      );

      // Fetch the updated delivery since updateData only returns bool
      return await getPackageDeliveryById(orderId);
    } catch (e) {
      throw ServerException('Failed to update package delivery: $e');
    }
  }

  @override
  Future<void> deletePackageDelivery(String orderId) async {
    try {
      await _apiService.deleteData(
        endPoint: ApiEndpoints.deleteDelivery,
        pathParams: {'order_id': orderId},
      );
    } catch (e) {
      throw ServerException('Failed to delete package delivery: $e');
    }
  }
}
