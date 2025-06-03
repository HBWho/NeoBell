import '../../../../core/constants/api_constants.dart';
import '../../../../core/data/api_service.dart';
import '../../../../core/error/server_exception.dart';
import '../models/device_model.dart';
import '../models/device_user_model.dart';

abstract interface class DeviceRemoteDataSource {
  Future<List<DeviceModel>> getDevices(String jwtToken);
  Future<DeviceModel> getDeviceDetails(String jwtToken, String sbcId);
  Future<DeviceModel> updateDeviceDetails(
      String jwtToken, String sbcId, String newName);
  Future<void> deleteDevice(String jwtToken, String sbcId);
  Future<List<DeviceUserModel>> getDeviceUsers(String jwtToken, String sbcId);
  Future<DeviceUserModel> addDeviceUser(
      String jwtToken, String sbcId, String email, String role);
  Future<void> removeDeviceUser(String jwtToken, String sbcId, String userId);
}

class DeviceRemoteDataSourceImpl implements DeviceRemoteDataSource {
  final ApiService _apiService;

  DeviceRemoteDataSourceImpl({required ApiService apiService})
      : _apiService = apiService;

  @override
  Future<List<DeviceModel>> getDevices(String jwtToken) async {
    try {
      final response = await _apiService.getData(
        endPoint: ApiEndpoints.getDevices,
      );

      final List<dynamic> devicesJson = response['items'] as List<dynamic>;
      return devicesJson.map((json) => DeviceModel.fromJson(json)).toList();
    } on ServerException {
      rethrow;
    }
  }

  @override
  Future<DeviceModel> getDeviceDetails(String jwtToken, String sbcId) async {
    try {
      final response = await _apiService.getData(
        endPoint: ApiEndpoints.getDeviceDetails,
        pathParams: {'sbc_id': sbcId},
      );

      return DeviceModel.fromJson(response);
    } on ServerException {
      rethrow;
    }
  }

  @override
  Future<DeviceModel> updateDeviceDetails(
      String jwtToken, String sbcId, String newName) async {
    try {
      final response = await _apiService.updateData(
        endPoint: ApiEndpoints.updateDevice,
        pathParams: {'sbc_id': sbcId},
        body: {'device_friendly_name': newName},
      );

      if (response) {
        return DeviceModel.fromJson({
          'sbc_id': sbcId,
          'device_friendly_name': newName,
          'last_updated_app_at': DateTime.now().toIso8601String(),
        });
      } else {
        throw ServerException('Failed to update device details');
      }
    } on ServerException {
      rethrow;
    }
  }

  @override
  Future<void> deleteDevice(String jwtToken, String sbcId) async {
    try {
      await _apiService.deleteData(
        endPoint: ApiEndpoints.deleteDevice,
        pathParams: {'sbc_id': sbcId},
      );
    } on ServerException {
      rethrow;
    }
  }

  @override
  Future<List<DeviceUserModel>> getDeviceUsers(
      String jwtToken, String sbcId) async {
    try {
      final response = await _apiService.getData(
        endPoint: ApiEndpoints.getDeviceUsers,
        pathParams: {'sbc_id': sbcId},
      );

      final List<dynamic> usersJson = response['items'] as List<dynamic>;
      return usersJson.map((json) => DeviceUserModel.fromJson(json)).toList();
    } on ServerException {
      rethrow;
    }
  }

  @override
  Future<DeviceUserModel> addDeviceUser(
      String jwtToken, String sbcId, String email, String role) async {
    try {
      final response = await _apiService.postData(
        endPoint: ApiEndpoints.addDeviceUser,
        pathParams: {'sbc_id': sbcId},
        body: {
          'email_of_invitee': email,
          'role': role,
        },
      );

      return DeviceUserModel.fromJson(response);
    } on ServerException {
      rethrow;
    }
  }

  @override
  Future<void> removeDeviceUser(
      String jwtToken, String sbcId, String userId) async {
    try {
      await _apiService.deleteData(
        endPoint: ApiEndpoints.removeDeviceUser,
        pathParams: {
          'sbc_id': sbcId,
          'user_id': userId,
        },
      );
    } on ServerException {
      rethrow;
    }
  }
}
