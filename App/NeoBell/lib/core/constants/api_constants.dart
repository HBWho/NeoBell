class ApiConstants {
  static const String defaultUrl = 'http://147.93.36.151:5000';
}

enum ApiEndpoints {
  // --- Authentication & User ---
  login('auth/login'), // POST
  // createLogin might be 'auth/register' or 'users' depending on your flow
  registerUser('users/register'), // POST (if self-registration)
  // updateLogin might be 'users/me/password' or 'users/me/credentials'
  updatePassword('users/me/password'), // PUT/PATCH
  getMyUser(
      'users/me'), // GET (gets the currently authenticated user's details)
  updateMyUser('users/me'), // PUT/PATCH (update user profile details)
  logout('auth/logout'), // POST (can invalidate token on server-side)

  // --- NeoBell Device Management & Settings ---
  // Assuming a user can have one or more NeoBell devices.
  // If a user has only one, 'devices/mine' could be an alias or primary.
  getMyDevice(
      'devices/mine'), // GET (gets the primary NeoBell device associated with the user)
  // getDeviceById('devices/{deviceId}'),  // GET (if users can have multiple devices)
  updateDeviceSettings('devices/{deviceId}/settings'), // PUT/PATCH
  // Example settings: notification preferences, DND mode
  // rebootDevice('devices/{deviceId}/reboot'), // POST (Example advanced action)

  // --- Video Messages (Records) ---
  getVideoMessages(
      'devices/{deviceId}/videomessages'), // GET (list of video messages with pagination, filters for date, read/unread)
  getVideoMessageById(
      'videomessages/{messageId}'), // GET (get specific video message details, including S3 URL)
  markVideoMessageAsRead('videomessages/{messageId}/read'), // PUT or PATCH
  deleteVideoMessage('videomessages/{messageId}'), // DELETE

  // --- Package Deliveries (Records) ---
  getDeliveryLogs(
      'devices/{deviceId}/deliveries'), // GET (list of delivery attempts/logs with pagination, filters)
  getDeliveryLogById(
      'deliveries/{deliveryId}'), // GET (details of a specific delivery)
  // deleteDeliveryLog('deliveries/{deliveryId}'), // DELETE (if users can clear logs)

  // --- Expected Deliveries (User Input) ---
  createExpectedDelivery('users/me/expected-deliveries'), // POST
  getExpectedDeliveries(
      'users/me/expected-deliveries'), // GET (list current/upcoming expected deliveries)
  updateExpectedDelivery('expected-deliveries/{expectedDeliveryId}'), // PUT
  deleteExpectedDelivery('expected-deliveries/{expectedDeliveryId}'), // DELETE

  // --- Visitor Permissions ---
  getVisitorPermissions(
      'devices/{deviceId}/visitor-permissions'), // GET (list allowed/blocked visitors)
  addVisitorPermission('devices/{deviceId}/visitor-permissions'), // POST
  updateVisitorPermission(
      'visitor-permissions/{permissionId}'), // PUT (e.g., change from allow to block, update name)
  deleteVisitorPermission('visitor-permissions/{permissionId}'), // DELETE

  // --- Access Logs (General event logs beyond just video/delivery) ---
  getAccessLogs(
      'devices/{deviceId}/access-logs'), // GET (doorbell rings, unknown persons, etc.)

  // --- Notifications ---
  updateFirebaseToken(
      'users/me/fcm-token'); // POST or PUT (to register/update the device token for push notifications)

  // --- Potentially for initiating actions on the NeoBell device ---
  // These would trigger an action on the device via the backend.
  // E.g., if the user wants to remotely trigger the "leave a message" flow if someone is detected but hasn't interacted.
  // triggerLeaveMessage('devices/{deviceId}/actions/prompt-leave-message'), // POST
  // triggerUnlockCompartment1('devices/{deviceId}/actions/unlock-compartment1'); // POST (IF this feature is desired and secure)

  final String path;
  const ApiEndpoints(this.path);
}
