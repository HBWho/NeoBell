import '../../../../core/constants/api_constants.dart';
import '../../../../core/data/api_service.dart';
import '../../../../core/error/server_exception.dart';
import '../models/nfc_tag_model.dart';
import '../models/user_profile_model.dart';

abstract class UserProfileRemoteDataSource {
  Future<UserProfileModel> getCurrentProfile();
  Future<UserProfileModel> updateProfile({required String name});
  Future<void> updateDeviceToken({required String deviceToken});
  Future<void> registerNfcTag({
    required String tagId,
    required String friendlyName,
  });
  Future<void> updateNfcTag({
    required String tagId,
    required String friendlyName,
  });
  Future<void> removeNfcTag({required String tagId});
  Future<List<NfcTagModel>> getNfcTags();
}

class UserProfileRemoteDataSourceImpl implements UserProfileRemoteDataSource {
  final ApiService _apiService;

  UserProfileRemoteDataSourceImpl(this._apiService);

  @override
  Future<UserProfileModel> getCurrentProfile() async {
    try {
      final response = await _apiService.getData(
        endPoint: ApiEndpoints.getUserProfile,
      );
      return UserProfileModel.fromJson(response);
    } on ServerException {
      rethrow;
    } catch (e) {
      throw ServerException('Failed to convert profile data to model');
    }
  }

  @override
  Future<UserProfileModel> updateProfile({required String name}) async {
    try {
      final response = await _apiService.updateData(
        endPoint: ApiEndpoints.updateUserProfile,
        body: {'name': name},
      );
      if (response) {
        return getCurrentProfile();
      }
      throw ServerException('Failed to update profile');
    } catch (e) {
      throw ServerException('Failed to update profile');
    }
  }

  @override
  Future<void> updateDeviceToken({required String deviceToken}) async {
    try {
      await _apiService.postData(
        endPoint: ApiEndpoints.updateDeviceToken,
        body: {'push_notification_token': deviceToken},
      );
    } catch (e) {
      throw ServerException('Failed to update device token');
    }
  }

  @override
  Future<void> registerNfcTag({
    required String tagId,
    required String friendlyName,
  }) async {
    try {
      await _apiService.postData(
        endPoint: ApiEndpoints.registerNfcTag,
        body: {'nfc_id_scanned': tagId, "tag_friendly_name": friendlyName},
      );
    } catch (e) {
      throw ServerException('Failed to register NFC tag');
    }
  }

  @override
  Future<void> updateNfcTag({
    required String tagId,
    required String friendlyName,
  }) async {
    try {
      await _apiService.updateData(
        endPoint: ApiEndpoints.updateNfcTag,
        pathParams: {'nfc_id_scanned': tagId},
        body: {'tag_friendly_name': friendlyName},
      );
    } catch (e) {
      throw ServerException('Failed to update NFC tag');
    }
  }

  @override
  Future<void> removeNfcTag({required String tagId}) async {
    try {
      await _apiService.deleteData(
        endPoint: ApiEndpoints.deleteNfcTag,
        pathParams: {'nfc_id_scanned': tagId},
      );
    } catch (e) {
      throw ServerException('Failed to remove NFC tag');
    }
  }

  @override
  Future<List<NfcTagModel>> getNfcTags() async {
    try {
      final response = await _apiService.getData(
        endPoint: ApiEndpoints.listNfcTags,
      );
      final List<dynamic> tags = response['tags'] ?? [];
      return tags.map((tag) => NfcTagModel.fromJson(tag)).toList();
    } catch (e) {
      throw ServerException('Failed to get NFC tags');
    }
  }
}
