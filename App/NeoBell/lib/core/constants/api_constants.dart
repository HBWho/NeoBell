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
  deleteMessage('messages/{message_id}'),

  // Package Deliveries endpoints
  getDeliveries('deliveries'),
  createDelivery('deliveries'),
  getDeliveryDetails('deliveries/{order_id}'),
  updateDelivery('deliveries/{order_id}'),
  deleteDelivery('deliveries/{order_id}'),

  // Visitor Permissions endpoints
  getVisitorPermissions('visitors'),
  generateVisitorImageUrl('visitors/{face_tag_id}/image-url'),
  updateVisitorPermission('visitors/{face_tag_id}'),
  deleteVisitorPermission('visitors/{face_tag_id}'),

  // Activity Logs endpoints
  getActivityLogs('activity-logs'),
  getActivityLogDetails('activity-logs/{log_source_id}/{timestamp_uuid}');

  final String path;
  const ApiEndpoints(this.path);
}
