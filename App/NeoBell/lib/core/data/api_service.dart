import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:image_picker/image_picker.dart';
import 'package:logger/logger.dart';
import 'package:http/http.dart' as http;

import '../constants/api_constants.dart';
import '../error/auth_exception.dart';
import '../error/server_exception.dart';
import '../services/auth_interceptor_service.dart';
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

  Future<void> sendImage({
    required ApiEndpoints endPoint,
    required XFile image,
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
        header: headers.toString(),
        body: '',
      );

      final response = await http.get(uri, headers: headers);
      await _statusHandler(response);
      return jsonDecode(response.body) as Map<String, dynamic>;
    } on AuthException catch (e) {
      if (e.isLoggedIn) {
        // Retry the request once after successful reauth
        final uri = _buildUri(endPoint, pathParams, queryParams);
        final headers = await _buildHeadersWithAuth(header);
        final response = await http.get(uri, headers: headers);
        await _statusHandler(response);
        return jsonDecode(response.body) as Map<String, dynamic>;
      }
      throw ServerException(e.message);
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
        header: headers.toString(),
        body: body.toString(),
      );

      final response = await http.post(
        uri,
        headers: headers,
        body: jsonEncode(body),
      );
      await _statusHandler(response);
      return jsonDecode(response.body) as Map<String, dynamic>;
    } on AuthException catch (e) {
      if (e.isLoggedIn) {
        // Retry the request once after successful reauth
        final uri = _buildUri(endPoint, pathParams);
        final headers = await _buildHeadersWithAuth(header);
        final response = await http.post(
          uri,
          headers: headers,
          body: jsonEncode(body),
        );
        await _statusHandler(response);
        return jsonDecode(response.body) as Map<String, dynamic>;
      }
      throw ServerException(e.message);
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
        header: headers.toString(),
        body: body.toString(),
      );

      final response = await http.put(
        uri,
        headers: headers,
        body: jsonEncode(body),
      );
      await _statusHandler(response);
      return true;
    } on AuthException catch (e) {
      if (e.isLoggedIn) {
        // Retry the request once after successful reauth
        final uri = _buildUri(endPoint, pathParams);
        final headers = await _buildHeadersWithAuth(header);
        final response = await http.put(
          uri,
          headers: headers,
          body: jsonEncode(body),
        );
        await _statusHandler(response);
        return true;
      }
      throw ServerException(e.message);
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
        header: headers.toString(),
        body: body.toString(),
      );

      final response = await http.delete(
        uri,
        headers: headers,
        body: jsonEncode(body),
      );
      await _statusHandler(response);
    } on AuthException catch (e) {
      if (e.isLoggedIn) {
        // Retry the request once after successful reauth
        final uri = _buildUri(endPoint, pathParams);
        final headers = await _buildHeadersWithAuth(header);
        final response = await http.delete(
          uri,
          headers: headers,
          body: jsonEncode(body),
        );
        await _statusHandler(response);
        return;
      }
      throw ServerException(e.message);
    } catch (e) {
      _logger.e('An error occurred while deleting data: $e');
      throw ServerException(e.toString());
    }
  }

  @override
  Future<void> sendImage({
    required ApiEndpoints endPoint,
    required XFile image,
    Map<String, String>? header,
    Map<String, String>? pathParams,
  }) async {
    try {
      final uri = _buildUri(endPoint, pathParams);
      final headers = await _buildHeadersWithAuth(header);
      final request =
          http.MultipartRequest('POST', uri)
            ..headers.addAll(headers)
            ..files.add(await http.MultipartFile.fromPath('image', image.path));

      _debugSendPrint(
        path: uri.toString(),
        header: headers.toString(),
        body: '',
      );
      final streamedResponse = await request.send();
      final response = await http.Response.fromStream(streamedResponse);
      await _statusHandler(response);
    } on AuthException catch (e) {
      if (e.isLoggedIn) {
        // Retry the request once after successful reauth
        final uri = _buildUri(endPoint, pathParams);
        final headers = await _buildHeadersWithAuth(header);
        final request =
            http.MultipartRequest('POST', uri)
              ..headers.addAll(headers)
              ..files.add(
                await http.MultipartFile.fromPath('image', image.path),
              );

        final streamedResponse = await request.send();
        final response = await http.Response.fromStream(streamedResponse);
        await _statusHandler(response);
        return;
      }
      throw ServerException(e.message);
    } catch (e) {
      _logger.e('An error occurred while sending image: $e');
      throw ServerException(e.toString());
    }
  }

  void _debugSendPrint({String? path, String? body, String? header}) {
    if (kDebugMode) {
      _logger.d(
        'Sending request to $path\n'
        'Header: $header\n'
        'Body: $body',
      );
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
    final statusCode =
        errorData['error']['code'] != null
            ? '${response.statusCode}: ${errorData['error']['code']}'
            : response.statusCode.toString();
    final errorMessage = errorData['error']['message'] ?? 'Ocorreu um erro';
    final errorDetails = errorData['error']['details'] ?? '';
    _logger.e(
      'Request failed. Status code: $statusCode\n'
      'Message: $errorMessage\n'
      'Details: $errorDetails',
    );

    throw ServerException('$statusCode, $errorMessage. $errorDetails');
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
