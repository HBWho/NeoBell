import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:logger/logger.dart';
import 'package:http/http.dart' as http;

import '../constants/api_constants.dart';
import '../error/server_exception.dart';
import '../services/token_manager.dart';

abstract interface class ApiService {
  Future<Map<String, dynamic>> getData({
    required ApiEndpoints endPoint,
    Map<String, String>? header,
    Map<String, String>? pathParams,
    Map<String, String>? queryParams,
  });

  Future<Map<String, dynamic>> postData({
    required ApiEndpoints endPoint,
    Map<String, dynamic>? body,
    Map<String, String>? header,
    Map<String, String>? pathParams,
  });

  Future<bool> updateData({
    required ApiEndpoints endPoint,
    required Map<String, dynamic> body,
    Map<String, String>? header,
    Map<String, String>? pathParams,
  });

  Future<void> deleteData({
    required ApiEndpoints endPoint,
    Map<String, dynamic>? body,
    Map<String, String>? header,
    Map<String, String>? pathParams,
  });
}

class ApiServiceImpl implements ApiService {
  static final _logger = Logger();
  final TokenManager _tokenManager;

  ApiServiceImpl({required TokenManager tokenManager})
    : _tokenManager = tokenManager;

  Future<Map<String, String>> _buildHeadersWithAuth([
    Map<String, String>? extraHeaders,
  ]) async {
    final token = await _tokenManager.getValidToken();
    return {
      'Authorization': 'Bearer $token',
      'Accept': 'application/json',
      'Content-Type': 'application/json',
      ...?extraHeaders,
    };
  }

  @override
  Future<Map<String, dynamic>> getData({
    required ApiEndpoints endPoint,
    Map<String, String>? header,
    Map<String, String>? pathParams,
    Map<String, String>? queryParams,
  }) async {
    try {
      final uri = _buildUri(endPoint, pathParams, queryParams);
      final headers = await _buildHeadersWithAuth(header);
      _debugSendPrint(
        path: uri.toString(),
        header: Map<String, String>.from(headers),
        body: '',
        requestType: 'GET',
      );

      final response = await http.get(uri, headers: headers);
      await _statusHandler(response);
      return jsonDecode(response.body) as Map<String, dynamic>;
    } on ServerException {
      rethrow;
    } catch (e) {
      _logger.e('An error occurred while getting data: $e');
      throw ServerException(e.toString());
    }
  }

  @override
  Future<Map<String, dynamic>> postData({
    required ApiEndpoints endPoint,
    Map<String, dynamic>? body,
    Map<String, String>? header,
    Map<String, String>? pathParams,
  }) async {
    try {
      final uri = _buildUri(endPoint, pathParams);
      final headers = await _buildHeadersWithAuth(header);
      _debugSendPrint(
        path: uri.toString(),
        header: Map<String, String>.from(headers),
        body: body.toString(),
        requestType: 'POST',
      );

      final response = await http.post(
        uri,
        headers: headers,
        body: jsonEncode(body),
      );
      await _statusHandler(response);
      return jsonDecode(response.body) as Map<String, dynamic>;
    } on ServerException {
      rethrow;
    } catch (e) {
      _logger.e('An error occurred while posting data: $e');
      throw ServerException(e.toString());
    }
  }

  @override
  Future<bool> updateData({
    required ApiEndpoints endPoint,
    required Map<String, dynamic> body,
    Map<String, String>? header,
    Map<String, String>? pathParams,
  }) async {
    try {
      final uri = _buildUri(endPoint, pathParams);
      final headers = await _buildHeadersWithAuth(header);
      _debugSendPrint(
        path: uri.toString(),
        header: Map<String, String>.from(headers),
        body: body.toString(),
        requestType: 'PUT',
      );

      final response = await http.put(
        uri,
        headers: headers,
        body: jsonEncode(body),
      );
      await _statusHandler(response);
      return true;
    } on ServerException {
      rethrow;
    } catch (e) {
      _logger.e('An error occurred while updating data: $e');
      throw ServerException(e.toString());
    }
  }

  @override
  Future<void> deleteData({
    required ApiEndpoints endPoint,
    Map<String, dynamic>? body,
    Map<String, String>? header,
    Map<String, String>? pathParams,
  }) async {
    try {
      final uri = _buildUri(endPoint, pathParams);
      final headers = await _buildHeadersWithAuth(header);
      _debugSendPrint(
        path: uri.toString(),
        header: Map<String, String>.from(headers),
        body: body.toString(),
        requestType: 'DELETE',
      );

      final response = await http.delete(
        uri,
        headers: headers,
        body: jsonEncode(body),
      );
      await _statusHandler(response);
    } on ServerException {
      rethrow;
    } catch (e) {
      _logger.e('An error occurred while deleting data: $e');
      throw ServerException(e.toString());
    }
  }

  void _debugSendPrint({
    String? path,
    String? body,
    Map<String, String>? header,
    String? requestType,
  }) {
    if (kDebugMode) {
      header?.remove('Authorization');
      _logger.d(
        'Sending request to $path\n'
        'Request Type: $requestType\n'
        'Header: $header\n'
        'Body: $body',
      );
    }
  }

  Future<void> _statusHandler(http.Response response) async {
    if (kDebugMode) {
      _logger.d(
        'Server Response, Status code: ${response.statusCode}, Body: ${response.body}',
      );
    }
    final List<int> validStatusCodes = [200, 201, 204, 202];
    if (validStatusCodes.contains(response.statusCode)) {
      _logger.i('Request successful with status code: ${response.statusCode}');
      return;
    }

    final errorData = jsonDecode(response.body);
    final errorMessage = errorData['message'] ?? 'Unknown error occurred';
    final errorDetails = errorData['error'] ?? '';
    _logger.e(
      'Request failed. Status code: ${response.statusCode}\n'
      'Message: $errorMessage\n'
      'Details: $errorDetails',
    );

    throw ServerException(
      '${response.statusCode}, $errorMessage. $errorDetails',
    );
  }

  Uri _buildUri(
    ApiEndpoints endPoint,
    Map<String, String>? pathParameters, [
    Map<String, String>? queryParameters,
  ]) {
    final String baseUrl = ApiConstants.defaultUrl;
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
