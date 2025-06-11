import '../../../../core/constants/api_constants.dart';
import '../../../../core/data/api_service.dart';
import '../../../../core/error/server_exception.dart';
import '../models/device_model.dart';
import '../models/device_user_model.dart';

abstract interface class DeviceRemoteDataSource {
  Future<List<DeviceModel>> getDevices({int? limit, String? lastEvaluatedKey});

  Future<DeviceModel> getDeviceDetails(String sbcId);

  Future<DeviceModel> updateDevice(String sbcId, String deviceFriendlyName);

  Future<void> deleteDevice(String sbcId);

  Future<List<DeviceUserModel>> getDeviceUsers(String sbcId);

  Future<void> addDeviceUser(String sbcId, String userEmail);

  Future<void> removeDeviceUser(String sbcId, String userId);
}

class DeviceRemoteDataSourceImpl implements DeviceRemoteDataSource {
  final ApiService _apiService;

  DeviceRemoteDataSourceImpl(this._apiService);

  @override
  Future<List<DeviceModel>> getDevices({
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

      final response = await _apiService.getData(
        endPoint: ApiEndpoints.getDevices,
        queryParams: queryParams.isNotEmpty ? queryParams : null,
      );

      final items = response['items'] as List<dynamic>;
      return items
          .map((item) => DeviceModel.fromJson(item as Map<String, dynamic>))
          .toList();
    } catch (e) {
      throw ServerException(e.toString());
    }
  }

  @override
  Future<DeviceModel> getDeviceDetails(String sbcId) async {
    try {
      final response = await _apiService.getData(
        endPoint: ApiEndpoints.getDeviceDetails,
        pathParams: {'sbc_id': sbcId},
      );

      return DeviceModel.fromJson(response);
    } catch (e) {
      throw ServerException(e.toString());
    }
  }

  @override
  Future<DeviceModel> updateDevice(
    String sbcId,
    String deviceFriendlyName,
  ) async {
    try {
      await _apiService.updateData(
        endPoint: ApiEndpoints.updateDevice,
        pathParams: {'sbc_id': sbcId},
        body: {'device_friendly_name': deviceFriendlyName},
      );

      // Return a basic device model since the API might not return the full device
      return DeviceModel(
        sbcId: sbcId,
        deviceFriendlyName: deviceFriendlyName,
        roleOnDevice: 'Owner', // Placeholder
        status: 'active', // Placeholder
      );
    } catch (e) {
      throw ServerException(e.toString());
    }
  }

  @override
  Future<void> deleteDevice(String sbcId) async {
    try {
      await _apiService.deleteData(
        endPoint: ApiEndpoints.deleteDevice,
        pathParams: {'sbc_id': sbcId},
      );
    } catch (e) {
      throw ServerException(e.toString());
    }
  }

  @override
  Future<List<DeviceUserModel>> getDeviceUsers(String sbcId) async {
    try {
      final response = await _apiService.getData(
        endPoint: ApiEndpoints.getDeviceUsers,
        pathParams: {'sbc_id': sbcId},
      );

      final items = response['items'] as List<dynamic>;
      return items
          .map((item) => DeviceUserModel.fromJson(item as Map<String, dynamic>))
          .toList();
    } catch (e) {
      throw ServerException(e.toString());
    }
  }

  @override
  Future<void> addDeviceUser(String sbcId, String userEmail) async {
    try {
      await _apiService.postData(
        endPoint: ApiEndpoints.addDeviceUser,
        pathParams: {'sbc_id': sbcId},
        body: {'email_of_invitee': userEmail, 'role': 'Resident'},
      );
    } catch (e) {
      throw ServerException(e.toString());
    }
  }

  @override
  Future<void> removeDeviceUser(String sbcId, String userId) async {
    try {
      await _apiService.deleteData(
        endPoint: ApiEndpoints.removeDeviceUser,
        pathParams: {'sbc_id': sbcId, 'user_id': userId},
      );
    } catch (e) {
      throw ServerException(e.toString());
    }
  }
}
