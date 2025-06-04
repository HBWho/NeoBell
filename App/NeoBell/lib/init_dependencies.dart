part of 'init_dependencies_imports.dart';

final serviceLocator = GetIt.instance;

enum InitDependenciesType { prod, dev }

class InitDependencies {
  static String type = InitDependenciesType.prod.name;
  static Future<void> init() async {
    // * Core
    // Http Client
    serviceLocator.registerLazySingleton(() => http.Client());

    // Local Data
    serviceLocator
      ..registerLazySingleton<LocalStorageRepository>(
        () => LocalStorageRepositoryImpl(),
        instanceName: 'non-secure',
      )
      ..registerLazySingleton<LocalStorageRepository>(
        () => SecureStorageRepositoryImpl(),
        instanceName: 'secure',
      );

    // Token Management
    serviceLocator
      ..registerLazySingleton<TokenRepository>(() => TokenRepositoryImpl())
      ..registerLazySingleton<TokenManager>(
        () => TokenManagerImpl(
          tokenRepository: serviceLocator<TokenRepository>(),
        ),
      );

    // Api
    serviceLocator.registerLazySingleton<ApiService>(
      () => ApiServiceImpl(tokenManager: serviceLocator<TokenManager>()),
    );

    _initAuth();
    _initNotifications();
    _initUserProfile();
    _initVideoMessages();
    _initVisitorPermissions();
    _initDeviceManagement();
    _initActivityLogs();
  }

  static void _initAuth() {
    serviceLocator
      // DataSources
      ..registerLazySingleton<AuthRepository>(
        () => CognitoAuthRepository(),
        instanceName: InitDependenciesType.prod.name,
      )
      // UseCases
      ..registerFactory(
        () => SignIn(serviceLocator<AuthRepository>(instanceName: type)),
      )
      ..registerFactory(
        () => SignOut(serviceLocator<AuthRepository>(instanceName: type)),
      )
      ..registerFactory(
        () =>
            CheckAuthStatus(serviceLocator<AuthRepository>(instanceName: type)),
      )
      // Cubit
      ..registerLazySingleton(
        () => AuthCubit(
          signIn: serviceLocator<SignIn>(),
          signOut: serviceLocator<SignOut>(),
          checkAuthStatus: serviceLocator<CheckAuthStatus>(),
          tokenManager: serviceLocator<TokenManager>(),
          userProfileCubit: serviceLocator<UserProfileCubit>(),
          notificationCubit: serviceLocator<NotificationCubit>(),
        ),
      );
  }

  static void _initNotifications() {
    serviceLocator
      // Plugins
      ..registerLazySingleton<FlutterLocalNotificationsPlugin>(
        () => FlutterLocalNotificationsPlugin(),
      )
      ..registerLazySingleton<FirebaseMessaging>(
        () => FirebaseMessaging.instance,
      )
      // DataSources
      ..registerLazySingleton<LocalNotificationsDataSource>(
        () => LocalNotificationsDataSourceImpl(
          serviceLocator<FlutterLocalNotificationsPlugin>(),
        ),
      )
      ..registerLazySingleton<NotificationRemoteDataSource>(
        () => NotificationRemoteDataSourceImpl(
          localNotifications: serviceLocator<LocalNotificationsDataSource>(),
          firebaseMessaging: serviceLocator<FirebaseMessaging>(),
        ),
      )
      // Repository
      ..registerFactory<NotificationRepository>(
        () => NotificationRepositoryImpl(
          serviceLocator<NotificationRemoteDataSource>(),
        ),
      )
      // UseCases
      ..registerFactory(
        () => InitializeNotifications(serviceLocator<NotificationRepository>()),
      )
      ..registerFactory(
        () => ShowNotification(serviceLocator<NotificationRepository>()),
      )
      ..registerFactory(
        () => GetFirebaseToken(serviceLocator<NotificationRepository>()),
      )
      // Cubit
      ..registerLazySingleton(
        () => NotificationCubit(
          initializeNotifications: serviceLocator<InitializeNotifications>(),
          showNotification: serviceLocator<ShowNotification>(),
          getFirebaseToken: serviceLocator<GetFirebaseToken>(),
        ),
      );
  }

  static void _initUserProfile() {
    serviceLocator
      // DataSource
      ..registerLazySingleton<UserProfileRemoteDataSource>(
        () => UserProfileRemoteDataSourceImpl(serviceLocator<ApiService>()),
        instanceName: InitDependenciesType.prod.name,
      )
      // Repository
      ..registerLazySingleton<UserProfileRepository>(
        () => UserProfileRepositoryImpl(
          serviceLocator<UserProfileRemoteDataSource>(instanceName: type),
        ),
      )
      // UseCases
      ..registerFactory(
        () => GetCurrentProfile(serviceLocator<UserProfileRepository>()),
      )
      ..registerFactory(
        () => UpdateProfile(serviceLocator<UserProfileRepository>()),
      )
      ..registerFactory(
        () => GetNfcTags(serviceLocator<UserProfileRepository>()),
      )
      ..registerFactory(
        () => RegisterNfcTag(serviceLocator<UserProfileRepository>()),
      )
      ..registerFactory(
        () => RemoveNfcTag(serviceLocator<UserProfileRepository>()),
      )
      ..registerFactory(
        () => UpdateDeviceToken(serviceLocator<UserProfileRepository>()),
      )
      ..registerFactory(
        () => UpdateNfcTag(serviceLocator<UserProfileRepository>()),
      )
      // Cubit
      ..registerLazySingleton(
        () => UserProfileCubit(
          getCurrentProfile: serviceLocator<GetCurrentProfile>(),
          updateProfile: serviceLocator<UpdateProfile>(),
          getNfcTags: serviceLocator<GetNfcTags>(),
          registerNfcTag: serviceLocator<RegisterNfcTag>(),
          removeNfcTag: serviceLocator<RemoveNfcTag>(),
          updateDeviceToken: serviceLocator<UpdateDeviceToken>(),
          updateNfcTag: serviceLocator<UpdateNfcTag>(),
        ),
      );
  }

  static void _initVideoMessages() {
    serviceLocator
      // DataSource
      ..registerLazySingleton<VideoMessageRemoteDataSource>(
        () => VideoMessageRemoteDataSourceImpl(serviceLocator<ApiService>()),
        instanceName: InitDependenciesType.prod.name,
      )
      // Repository
      ..registerLazySingleton<VideoMessageRepository>(
        () => VideoMessageRepositoryImpl(
          serviceLocator<VideoMessageRemoteDataSource>(instanceName: type),
        ),
      )
      // UseCases
      ..registerFactory(
        () => DeleteMessage(serviceLocator<VideoMessageRepository>()),
      )
      ..registerFactory(
        () => GenerateViewUrl(serviceLocator<VideoMessageRepository>()),
      )
      ..registerFactory(
        () => GetVideoMessages(serviceLocator<VideoMessageRepository>()),
      )
      ..registerFactory(
        () => MarkAsViewed(serviceLocator<VideoMessageRepository>()),
      )
      // Bloc
      ..registerLazySingleton(
        () => VideoMessageBloc(
          deleteMessage: serviceLocator<DeleteMessage>(),
          generateViewUrl: serviceLocator<GenerateViewUrl>(),
          getVideoMessages: serviceLocator<GetVideoMessages>(),
          markAsViewed: serviceLocator<MarkAsViewed>(),
        ),
      );
  }

  static void _initVisitorPermissions() {
    serviceLocator
      // DataSource
      ..registerLazySingleton<VisitorPermissionRemoteDataSource>(
        () => VisitorPermissionRemoteDataSourceImpl(
          apiService: serviceLocator<ApiService>(),
        ),
        instanceName: InitDependenciesType.prod.name,
      )
      // Repository
      ..registerLazySingleton<VisitorPermissionRepository>(
        () => VisitorPermissionRepositoryImpl(
          remoteDataSource: serviceLocator<VisitorPermissionRemoteDataSource>(
            instanceName: type,
          ),
        ),
      )
      // UseCases
      ..registerFactory(
        () => GetVisitorPermissions(
          serviceLocator<VisitorPermissionRepository>(),
        ),
      )
      ..registerFactory(
        () => GetVisitorDetailsWithImage(
          serviceLocator<VisitorPermissionRepository>(),
        ),
      )
      ..registerFactory(
        () => UpdateVisitorPermission(
          serviceLocator<VisitorPermissionRepository>(),
        ),
      )
      ..registerFactory(
        () => DeleteVisitorPermission(
          serviceLocator<VisitorPermissionRepository>(),
        ),
      )
      // Bloc
      ..registerLazySingleton(
        () => VisitorPermissionBloc(
          getVisitorPermissions: serviceLocator<GetVisitorPermissions>(),
          getVisitorDetailsWithImage:
              serviceLocator<GetVisitorDetailsWithImage>(),
          updateVisitorPermission: serviceLocator<UpdateVisitorPermission>(),
          deleteVisitorPermission: serviceLocator<DeleteVisitorPermission>(),
        ),
      );
  }

  static void _initDeviceManagement() {
    serviceLocator
      // DataSource
      ..registerLazySingleton<DeviceRemoteDataSource>(
        () => DeviceRemoteDataSourceImpl(serviceLocator<ApiService>()),
        instanceName: InitDependenciesType.prod.name,
      )
      // Repository
      ..registerLazySingleton<DeviceRepository>(
        () => DeviceRepositoryImpl(
          serviceLocator<DeviceRemoteDataSource>(instanceName: type),
        ),
      )
      // UseCases
      ..registerFactory(() => GetDevices(serviceLocator<DeviceRepository>()))
      ..registerFactory(
        () => GetDeviceDetails(serviceLocator<DeviceRepository>()),
      )
      ..registerFactory(() => UpdateDevice(serviceLocator<DeviceRepository>()))
      ..registerFactory(
        () => GetDeviceUsers(serviceLocator<DeviceRepository>()),
      )
      ..registerFactory(() => AddDeviceUser(serviceLocator<DeviceRepository>()))
      ..registerFactory(
        () => RemoveDeviceUser(serviceLocator<DeviceRepository>()),
      )
      // Bloc
      ..registerLazySingleton(
        () => DeviceBloc(
          getDevices: serviceLocator<GetDevices>(),
          getDeviceDetails: serviceLocator<GetDeviceDetails>(),
          updateDevice: serviceLocator<UpdateDevice>(),
          getDeviceUsers: serviceLocator<GetDeviceUsers>(),
          addDeviceUser: serviceLocator<AddDeviceUser>(),
          removeDeviceUser: serviceLocator<RemoveDeviceUser>(),
        ),
      );
  }

  static void _initActivityLogs() {
    serviceLocator
      // DataSource
      ..registerLazySingleton<ActivityLogRemoteDataSource>(
        () => ActivityLogRemoteDataSourceImpl(serviceLocator<ApiService>()),
        instanceName: InitDependenciesType.prod.name,
      )
      // Repository
      ..registerLazySingleton<ActivityLogRepository>(
        () => ActivityLogRepositoryImpl(
          remoteDataSource: serviceLocator<ActivityLogRemoteDataSource>(
            instanceName: type,
          ),
        ),
      )
      // UseCases
      ..registerFactory(
        () => GetActivityLogs(serviceLocator<ActivityLogRepository>()),
      )
      // Bloc
      ..registerLazySingleton(
        () =>
            ActivityLogBloc(getActivityLogs: serviceLocator<GetActivityLogs>()),
      );
  }
}
