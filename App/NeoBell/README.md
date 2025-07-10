# NeoBell Mobile App

**Version:** 1.0.1+2  
**Platform:** Android  
**Framework:** Flutter 3.7.0+

## 📱 Overview

The NeoBell Mobile App is the primary user interface for the NeoBell smart residential reception system. Built with Flutter, this app provides residents with a comprehensive platform to manage their smart doorbell device, view video messages from visitors, control access permissions, and monitor all activities related to their home's entrance.

## 🏗️ Architecture

The app follows **Clean Architecture** principles with a clear separation of concerns:

```
lib/
├── core/                     # Shared infrastructure and utilities
│   ├── common/               # Common widgets and utilities
│   ├── constants/            # App constants and API endpoints
│   ├── data/                 # Core data layer (API service, repositories)
│   ├── domain/               # Core domain layer (repositories interfaces)
│   ├── error/                # Error handling and failure classes
│   ├── services/             # Core services (navigation, biometric, etc.)
│   ├── theme/                # App theming and styling
│   └── utils/                # Utility functions
└── features/                 # Feature-based modules
    ├── auth/                 # Authentication & authorization
    ├── activity_logs/        # Activity monitoring and logs
    ├── device_management/    # NeoBell device management
    ├── notifications/        # Push notifications handling
    ├── package_deliveries/   # Package delivery management
    ├── user_profile/         # User profile management
    ├── video_messages/       # Video message viewing and management
    └── visitor_permissions/  # Visitor access control
```

Each feature follows the same internal structure:
- **`data/`**: Models, data sources, and repository implementations
- **`domain/`**: Entities, repository interfaces, and use cases
- **`presentation/`**: UI screens, BLoC/Cubit state management, and widgets

## 🚀 Key Features

### 🔐 Authentication & Security
- **AWS Cognito Integration**: Secure user authentication and authorization
- **Biometric Authentication**: Fingerprint/Face ID support for quick access
- **Secure Token Management**: JWT token handling and refresh

### 📹 Video Messages
- **View Visitor Messages**: Watch video messages left by visitors
- **Message Management**: Mark as viewed, delete, and organize messages
- **Secure Streaming**: Protected video URLs with temporary access

### 🏠 Device Management
- **Multi-Device Support**: Manage multiple NeoBell devices
- **User Management**: Add/remove users with access to devices

### 👤 User Profile Management
- **Profile Control**: Update personal information including name and contact details
- **Password Management**: Secure password change functionality
- **Account Settings**: Manage account preferences and security settings

### 🏷️ NFC Tag Management
- **Tag Registration**: Register new NFC tags for secure compartment access
- **Tag Management**: Rename, update, or delete existing NFC tags
- **Secure Access Control**: NFC tags used by the SBC to unlock the secure package compartment

### 👥 Visitor Permissions
- **Access Control**: Grant or revoke visitor permissions
- **Facial Recognition**: Manage recognized visitor profiles

### 📦 Package Deliveries
- **Delivery Tracking**: Monitor expected and received packages
- **Delivery History**: View complete delivery logs

### 📊 Activity Monitoring
- **Real-time Logs**: View all device activities and events
- **Filtering & Search**: Find specific activities by date, type, or user
- **Detailed Reports**: Comprehensive activity breakdowns

### 🔔 Smart Notifications
- **Firebase Cloud Messaging**: Real-time push notifications
- **Local Notifications**: In-app notification management
- **Customizable Settings**: Control notification preferences

## 🛠️ Technical Stack

### Core Framework
- **Flutter 3.7.0+**: Cross-platform mobile development
- **Dart**: Programming language

### State Management
- **BLoC/Cubit**: Predictable state management
- **flutter_bloc 9.0.0**: BLoC implementation for Flutter

### Backend Integration
- **AWS Amplify**: Authentication and AWS service integration
- **amplify_auth_cognito**: Cognito authentication
- **HTTP**: RESTful API communication with AWS Lambda

### Navigation & Routing
- **GoRouter 14.4.1**: Declarative routing solution

### Hardware Integration
- **Camera**: Video recording and image capture
- **NFC**: Near Field Communication for access control
- **Biometrics**: Local authentication (fingerprint/face)
- **QR/Barcode Scanner**: Package tracking capabilities

### Notifications
- **Firebase Messaging**: Push notification delivery
- **Local Notifications**: In-app notification system

### Media & UI
- **Video Player**: Video message playback with custom controls
- **Responsive Design**: Adaptive UI for different screen sizes
- **Material Design**: Modern Android UI components

## 📋 Prerequisites

Before running the NeoBell app, ensure you have:

### Development Environment
- **Flutter SDK**: Version 3.7.0 or higher
- **Dart SDK**: Included with Flutter
- **Android Studio** or **VS Code** with Flutter extension
- **Android SDK**: API level 21 (Android 5.0) or higher

### Device Requirements
- **Android Device/Emulator**: Android 5.0 (API 21) or higher
- **Biometric Hardware**: For fingerprint/face authentication (optional)
- **Camera**: For QR code scanning and image capture
- **Internet Connection**: Required for AWS backend communication

### AWS Configuration
- Valid NeoBell backend deployment
- Cognito User Pool access
- API Gateway endpoints configured

## 🚀 Installation & Setup

### 1. Clone the Repository
```bash
git clone <repository-url>
cd NeoBell/App/NeoBell
```

### 2. Install Dependencies
```bash
flutter clean
flutter pub get
```

### 3. Generate App Icons & Splash Screen
```bash
# Generate app icons
dart run flutter_launcher_icons -f flutter_launcher_icons.yaml

# Generate splash screen
dart run flutter_native_splash:create --path=flutter_native_splash.yaml
```

### 4. Configure Firebase (Optional - for notifications)
- Place your `google-services.json` in [`android/app/`](android/app/)
- Follow Firebase setup documentation for Flutter

## 🎯 Running the Application

### Development Mode
```bash
# Run on connected device/emulator
flutter run

# Run with specific device
flutter run -d <device-id>

# Run in debug mode with hot reload
flutter run --debug
```

### Release Mode
```bash
# Run in release mode
flutter run --release
```

## 📦 Building for Production

### Build APK
```bash
# Build universal APK
flutter build apk

# Build APK for specific architectures
flutter build apk --target-platform android-arm,android-arm64,android-x64
```

### Using the Automated Script
The project includes a Windows batch script for automated APK generation:

```cmd
# Run the automated build script
generate-apk-version-android.cmd
```

This script will:
- Extract version from [`pubspec.yaml`](pubspec.yaml)
- Build the APK with multi-architecture support
- Copy and rename the APK to [`apk/NeoBell_<version>.apk`](apk/)

### Build App Bundle (Recommended for Play Store)
```bash
flutter build appbundle
```

## 🔧 Configuration

### API Configuration
Update the API endpoint in [`lib/core/constants/api_constants.dart`](lib/core/constants/api_constants.dart):

```dart
class ApiConstants {
  static const String defaultUrl = 'YOUR_API_GATEWAY_URL';
}
```

### AWS Cognito Configuration
The Cognito configuration is in [`lib/features/auth/core/auth_init.dart`](lib/features/auth/core/auth_init.dart). Update the configuration with your Cognito User Pool details:

```dart
"CognitoUserPool": {
    "Default": {
        "PoolId": "YOUR_USER_POOL_ID",
        "AppClientId": "YOUR_APP_CLIENT_ID",
        "Region": "YOUR_AWS_REGION"
    }
}
```

## 🧪 Testing

### Run Unit Tests
```bash
flutter test
```

### Run Integration Tests
```bash
flutter test integration_test/
```

## 📱 Permissions

The app requires the following Android permissions:

- **CAMERA**: QR code scanning and image capture
- **INTERNET**: API communication
- **USE_BIOMETRIC**: Biometric authentication
- **NFC**: Near Field Communication
- **POST_NOTIFICATIONS**: Push notifications
- **VIBRATE**: Notification feedback
- **RECEIVE_BOOT_COMPLETED**: Persistent notifications
- **USE_FULL_SCREEN_INTENT**: Lock screen notifications

## 🔄 State Management

The app uses BLoC/Cubit pattern for state management:

- **AuthCubit**: Authentication state and user session
- **VideoMessageBloc**: Video message management
- **DeviceBloc**: Device management operations
- **VisitorPermissionBloc**: Visitor access control
- **PackageDeliveryBloc**: Package delivery tracking
- **ActivityLogBloc**: Activity monitoring
- **NotificationCubit**: Notification handling
- **UserProfileCubit**: User profile management

## 🔐 Security Features

- **End-to-end Encryption**: Secure communication with AWS backend
- **Token Management**: Automatic JWT token refresh
- **Biometric Protection**: Local authentication for sensitive operations
- **Secure Storage**: Encrypted local data storage
- **Certificate Pinning**: API communication security

## 🐛 Troubleshooting

### Common Issues

1. **Build Failures**
   ```bash
   flutter clean
   flutter pub get
   flutter build apk
   ```

2. **Authentication Issues**
   - Verify Cognito configuration
   - Check internet connectivity
   - Clear app data and re-authenticate

3. **Notification Problems**
   - Verify Firebase configuration
   - Check notification permissions
   - Test with Firebase Console

4. **Camera/NFC Issues**
   - Verify hardware permissions
   - Test on physical device (not emulator)
   - Check Android permission settings

## 📚 Additional Resources

- [Flutter Documentation](https://docs.flutter.dev/)
- [AWS Amplify Flutter](https://docs.amplify.aws/flutter/start/)
- [Firebase for Flutter](https://firebase.google.com/docs/flutter/setup)
- [BLoC Library](https://bloclibrary.dev/)

## 📄 License

This project is part of the NeoBell smart residential reception system. All rights reserved.

---

**Note**: This app is designed to work in conjunction with the NeoBell hardware device and AWS backend infrastructure. Ensure all components are properly configured for full functionality.

**NeoBell** - Securely connected. Simply Home