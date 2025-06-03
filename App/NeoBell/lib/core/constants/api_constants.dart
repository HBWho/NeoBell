class ApiConstants {
  static const String defaultUrl =
      'https://swatx4x8nf.execute-api.us-east-1.amazonaws.com/dev';
}

enum ApiEndpoints {
  // User Profile endpoints
  getUserProfile('users/me'),
  updateUserProfile('users/me'),
  updateDeviceToken('users/device-token'),

  // NFC Tag Management endpoints
  registerNfcTag('users/me/nfc-tags'),
  listNfcTags('users/me/nfc-tags'),
  updateNfcTag('users/me/nfc-tags/{nfc_id_scanned}'),
  deleteNfcTag('users/me/nfc-tags/{nfc_id_scanned}'),

  // Device Management endpoints
  getDevices('devices'),
  getDeviceDetails('devices/{sbc_id}'),
  updateDevice('devices/{sbc_id}'),
  deleteDevice('devices/{sbc_id}'),
  getDeviceUsers('devices/{sbc_id}/users'),
  addDeviceUser('devices/{sbc_id}/users'),
  removeDeviceUser('devices/{sbc_id}/users/{user_id}'),

  // Video Messages endpoints
  getVideoMessages('messages'),
  generateViewUrl('messages/{message_id}/view-url'),
  markAsViewed('messages/{message_id}'),
  deleteMessage('messages/{message_id}');

  final String path;
  const ApiEndpoints(this.path);
}
