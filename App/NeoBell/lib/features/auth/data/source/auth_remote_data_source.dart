import '../../../../core/data/api_service.dart';
import '../../../../core/constants/api_constants.dart';
import '../../../../core/common/entities/user.dart';
import '../../../../core/error/server_exception.dart';

abstract interface class AuthRemoteDataSource {
  Future<User> login({
    required String username,
    required String password,
    required String firebaseToken,
  });
  Future<void> logout({required String jwtToken});
  Future<User> getUser({required String jwtToken});
}

class AuthRemoteDataSourceImpl implements AuthRemoteDataSource {
  final ApiService _apiService;
  AuthRemoteDataSourceImpl(this._apiService);

  @override
  Future<User> login(
      {required String username,
      required String password,
      required String firebaseToken}) async {
    try {
      final response = await _apiService.postData(
        endPoint: ApiEndpoints.login,
        body: {
          'username': username,
          'password': password,
          'firebase_token': firebaseToken
        },
      );
      if (response['jwt_token'] == null) {
        throw const ServerException('User is NULL');
      }
      response['username'] = username;
      response['password'] = password;
      return User.fromJson(response);
    } on ServerException {
      rethrow;
    } catch (e) {
      throw ServerException(e.toString());
    }
  }

  @override
  Future<void> logout({required String jwtToken}) async {
    try {
      await _apiService.deleteData(
        endPoint: ApiEndpoints.logout,
        jwtToken: jwtToken,
      );
    } on ServerException {
      rethrow;
    } catch (e) {
      throw ServerException(e.toString());
    }
  }

  @override
  Future<User> getUser({required String jwtToken}) async {
    try {
      final response = await _apiService.getData(
        endPoint: ApiEndpoints.getMyUser,
        jwtToken: jwtToken,
      );
      response['jwt_token'] = jwtToken;
      return User.fromJson(response);
    } on ServerException {
      rethrow;
    } catch (e) {
      throw ServerException(e.toString());
    }
  }
}
