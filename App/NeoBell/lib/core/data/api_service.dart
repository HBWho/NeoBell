import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:image_picker/image_picker.dart';
import 'package:logger/logger.dart';
import 'package:http/http.dart' as http;

import '../constants/api_constants.dart';
import '../domain/repositories/config_repository.dart';
import '../error/auth_exception.dart';
import '../error/server_exception.dart';
import '../services/auth_interceptor_service.dart';

abstract interface class ApiService {
  Future<Map<String, dynamic>> getData({
    required ApiEndpoints endPoint,
    required String jwtToken,
    Map<String, String>? header,
    Map<String, String>? pathParams,
    Map<String, String>? queryParams,
  });

  Future<Map<String, dynamic>> postData({
    required ApiEndpoints endPoint,
    String? jwtToken,
    Map<String, dynamic>? body,
    Map<String, String>? header,
    Map<String, String>? pathParams,
  });

  Future<bool> updateData({
    required ApiEndpoints endPoint,
    required String jwtToken,
    required Map<String, dynamic> body,
    Map<String, String>? header,
    Map<String, String>? pathParams,
  });

  Future<void> deleteData({
    required ApiEndpoints endPoint,
    required String jwtToken,
    Map<String, dynamic>? body,
    Map<String, String>? header,
    Map<String, String>? pathParams,
  });

  Future<void> sendImage({
    required ApiEndpoints endPoint,
    required String jwtToken,
    required XFile image,
    Map<String, String>? header,
    Map<String, String>? pathParams,
  });
}

class ApiServiceImpl implements ApiService {
  static final _logger = Logger();
  final ConfigRepository _configRepository;
  final AuthInterceptorService _authInterceptorService;

  ApiServiceImpl({
    required ConfigRepository configRepository,
    required AuthInterceptorService authInterceptorService,
  })  : _authInterceptorService = authInterceptorService,
        _configRepository = configRepository;

  @override
  Future<Map<String, dynamic>> getData({
    required ApiEndpoints endPoint,
    required String jwtToken,
    Map<String, String>? header,
    Map<String, String>? pathParams,
    Map<String, String>? queryParams,
  }) async {
    try {
      final uri = await _buildUri(endPoint, pathParams, queryParams);
      final Map<String, String> headers = {
        'Authorization': 'Bearer $jwtToken',
        'Accept': 'application/json',
        ...?header,
      };
      _debugSendPrint(
          path: uri.toString(), header: headers.toString(), body: '');
      final response = await http.get(uri, headers: headers);
      await _statusHandler(response);
      return jsonDecode(response.body) as Map<String, dynamic>;
    } on ServerException {
      rethrow;
    } on AuthException catch (e) {
      throw ServerException(e.message);
    } catch (e) {
      _logger.e('An error occurred while deleting data: $e');
      throw ServerException(e.toString());
    }
  }

  @override
  Future<Map<String, dynamic>> postData(
      {required ApiEndpoints endPoint,
      String? jwtToken,
      Map<String, dynamic>? body,
      Map<String, String>? header,
      Map<String, String>? pathParams}) async {
    try {
      final uri = await _buildUri(endPoint, pathParams);
      final Map<String, String> headers = {
        if (jwtToken != null) 'Authorization': 'Bearer $jwtToken',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        ...?header,
      };
      _debugSendPrint(
          path: uri.toString(),
          header: headers.toString(),
          body: body.toString());
      final response =
          await http.post(uri, headers: headers, body: jsonEncode(body));
      await _statusHandler(response);
      return jsonDecode(response.body) as Map<String, dynamic>;
    } on ServerException {
      rethrow;
    } on AuthException catch (e) {
      throw ServerException(e.message);
    } catch (e) {
      _logger.e('An error occurred while deleting data: $e');
      throw ServerException(e.toString());
    }
  }

  @override
  Future<bool> updateData(
      {required ApiEndpoints endPoint,
      required String jwtToken,
      required Map<String, dynamic> body,
      Map<String, String>? header,
      Map<String, String>? pathParams}) async {
    try {
      final uri = await _buildUri(endPoint, pathParams);
      final Map<String, String> headers = {
        'Authorization': 'Bearer $jwtToken',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        ...?header,
      };
      _debugSendPrint(
          path: uri.toString(),
          header: headers.toString(),
          body: body.toString());
      final response =
          await http.put(uri, headers: headers, body: jsonEncode(body));
      await _statusHandler(response);
      return true;
    } on ServerException {
      rethrow;
    } on AuthException catch (e) {
      throw ServerException(e.message);
    } catch (e) {
      _logger.e('An error occurred while deleting data: $e');
      throw ServerException(e.toString());
    }
  }

  @override
  Future<void> deleteData(
      {required ApiEndpoints endPoint,
      required String jwtToken,
      Map<String, dynamic>? body,
      Map<String, String>? header,
      Map<String, String>? pathParams}) async {
    try {
      final uri = await _buildUri(endPoint, pathParams);
      final Map<String, String> headers = {
        'Authorization': 'Bearer $jwtToken',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        ...?header,
      };
      _debugSendPrint(
          path: uri.toString(),
          header: headers.toString(),
          body: body.toString());
      final response =
          await http.delete(uri, headers: headers, body: jsonEncode(body));
      await _statusHandler(response);
    } on ServerException {
      rethrow;
    } on AuthException catch (e) {
      throw ServerException(e.message);
    } catch (e) {
      _logger.e('An error occurred while deleting data on server: $e');
      throw ServerException(e.toString());
    }
  }

  @override
  Future<void> sendImage(
      {required ApiEndpoints endPoint,
      required String jwtToken,
      required XFile image,
      Map<String, String>? header,
      Map<String, String>? pathParams}) async {
    try {
      final uri = await _buildUri(endPoint, pathParams);
      final Map<String, String> headers = {
        'Authorization': 'Bearer $jwtToken',
        'Accept': 'application/json',
        ...?header,
      };
      final request = http.MultipartRequest('POST', uri)
        ..headers.addAll(headers)
        ..files.add(await http.MultipartFile.fromPath('image', image.path));
      _debugSendPrint(
          path: uri.toString(), header: headers.toString(), body: '');
      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);
      await _statusHandler(response);
    } on ServerException {
      rethrow;
    } on AuthException catch (e) {
      throw ServerException(e.message);
    } catch (e) {
      _logger.e('An error occurred while sending image: $e');
      throw ServerException(e.toString());
    }
  }

  void _debugSendPrint({String? path, String? body, String? header}) {
    if (kDebugMode) {
      _logger.d('Sending request to $path\n'
          'Header: $header\n'
          'Body: $body');
    }
  }

  Future<void> _statusHandler(http.Response response) async {
    if (kDebugMode) {
      _logger.d('Server Response: ${response.body}');
    }
    if (response.statusCode == 200 || response.statusCode == 201) {
      _logger.i('Request successful');
      return;
    }

    final errorData = jsonDecode(response.body);
    final statusCode = errorData['error']['code'] != null
        ? '${response.statusCode}: ${errorData['error']['code']}'
        : response.statusCode.toString();
    final errorMessage = errorData['error']['message'] ?? 'Ocorreu um erro';
    final errorDetails = errorData['error']['details'] ?? '';
    _logger.e('Request failed. Status code: $statusCode\n'
        'Message: $errorMessage\n'
        'Details: $errorDetails');

    if (response.statusCode == 401) {
      final isLoggedIn = await _authInterceptorService.handleUnauthorized();
      if (isLoggedIn) {
        throw AuthException(isLoggedIn: true);
      }
      throw AuthException();
    }

    throw ServerException('$statusCode, $errorMessage. $errorDetails');
  }

  Future<Uri> _buildUri(
    ApiEndpoints endPoint,
    Map<String, String>? pathParameters, [
    Map<String, String>? queryParameters,
  ]) async {
    final String baseUrl = await _configRepository.getApiUrl();
    final String path = _buildPath(endPoint, pathParameters);
    return queryParameters != null && queryParameters.isEmpty
        ? Uri.parse('$baseUrl/$path')
        : Uri.parse('$baseUrl/$path').replace(queryParameters: queryParameters);
  }

  String _buildPath(ApiEndpoints requestType, Map<String, String>? pathParams) {
    String path = requestType.path;
    if (pathParams != null) {
      pathParams.forEach((key, value) {
        path = path.replaceAll('{$key}', value);
      });
    }
    return path;
  }
}
