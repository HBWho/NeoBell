part of 'init_dependencies_imports.dart';

final serviceLocator = GetIt.instance;

class InitDependencies {
  static const String type = 'prod';
  static Future<void> init() async {
    _initAuth();
    _initUserActions();
    _initLog();
    _initNotifications();

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
      )
      ..registerLazySingleton<ConfigRepository>(
        () => ConfigRepositoryImpl(
          nonSecureStorage: serviceLocator<LocalStorageRepository>(
              instanceName: 'non-secure'),
        ),
      )
      ..registerLazySingleton<SettingsCubit>(
        () => SettingsCubit(
          serviceLocator<ConfigRepository>(),
        ),
      );

    // Services
    serviceLocator.registerLazySingleton<AuthInterceptorService>(
      () => AuthInterceptorServiceImpl(),
    );

    // Api
    serviceLocator.registerLazySingleton<ApiService>(
      () => ApiServiceImpl(
        configRepository: serviceLocator<ConfigRepository>(),
        authInterceptorService: serviceLocator<AuthInterceptorService>(),
      ),
    );
    // Cubits
    serviceLocator.registerLazySingleton(() => UserCubit());
  }

  static void _initAuth() {
    serviceLocator
      // DataSources
      ..registerFactory<AuthRemoteDataSource>(
          () => AuthRemoteDataSourceImpl(serviceLocator<ApiService>()))
      // Repositories
      ..registerFactory<AuthRepository>(
          () => AuthRepositoryImpl(serviceLocator<AuthRemoteDataSource>()),
          instanceName: 'prod')
      ..registerFactory<AuthRepository>(
          () => AuthRepositoryImplMock(serviceLocator<AuthRemoteDataSource>()),
          instanceName: 'mock')
      ..registerFactory<AuthCredentialsRepository>(
        () => AuthCredentialsRepositoryImpl(
          serviceLocator<LocalStorageRepository>(instanceName: 'secure'),
        ),
      )
      // UseCases
      ..registerFactory(
          () => UserLogin(serviceLocator<AuthRepository>(instanceName: 'mock')))
      ..registerFactory(() =>
          UserLogout(serviceLocator<AuthRepository>(instanceName: 'mock')))
      ..registerFactory(() =>
          UserGetUser(serviceLocator<AuthRepository>(instanceName: 'mock')))
      // Blocs
      ..registerLazySingleton(() => AuthBloc(
            userCubit: serviceLocator<UserCubit>(),
            loginUseCase: serviceLocator<UserLogin>(),
            logoutUseCase: serviceLocator<UserLogout>(),
            getCurrentUseCase: serviceLocator<UserGetUser>(),
          ))
      // Cubics
      ..registerLazySingleton<AuthCredentialsCubit>(
        () => AuthCredentialsCubit(
          serviceLocator<AuthCredentialsRepository>(),
        ),
      );
  }

  static void _initUserActions() {
    serviceLocator
      // DataSources
      ..registerFactory<UserActionsRemoteDataSource>(
          () => UserActionsRemoteDataSourceImpl(serviceLocator<ApiService>()))
      // Repositories
      ..registerFactory<UserActionsRepository>(() => UserActionsRepositoryImpl(
          serviceLocator<UserActionsRemoteDataSource>()))
      // UseCases
      ..registerFactory(
          () => UserUpdateProfile(serviceLocator<UserActionsRepository>()))
      ..registerFactory(
          () => UserGetUserByUserName(serviceLocator<UserActionsRepository>()))
      ..registerFactory(
          () => UserRegisterUser(serviceLocator<UserActionsRepository>()))
      ..registerFactory(
          () => UserGetAllUsers(serviceLocator<UserActionsRepository>()))
      ..registerFactory(
          () => ChangeUserRoles(serviceLocator<UserActionsRepository>()))
      // Blocs
      ..registerLazySingleton(() => UserActionsBloc(
            userCubit: serviceLocator<UserCubit>(),
            updateUseCase: serviceLocator<UserUpdateProfile>(),
            registerUseCase: serviceLocator<UserRegisterUser>(),
            changeRolesUseCase: serviceLocator<ChangeUserRoles>(),
          ))
      ..registerLazySingleton(() => UserRequestBloc(
            userCubit: serviceLocator<UserCubit>(),
            userGetUserByUserName: serviceLocator<UserGetUserByUserName>(),
            userGetAllUsers: serviceLocator<UserGetAllUsers>(),
          ));
  }

  static void _initLog() {
    serviceLocator
      // Repositories
      ..registerFactory<LogRepository>(
        () => LogRepositoryImpl(serviceLocator<UserActionsRemoteDataSource>()),
      )
      // UseCases
      ..registerFactory(() => GetLogs(serviceLocator<LogRepository>()))
      // Blocs
      ..registerLazySingleton(() => LogBloc(
            getLogs: serviceLocator<GetLogs>(),
            userCubit: serviceLocator<UserCubit>(),
          ));
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
          apiService: serviceLocator<ApiService>(),
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
      ..registerFactory(
        () => UpdateFirebaseToken(serviceLocator<NotificationRepository>()),
      )
      // Cubit
      ..registerLazySingleton(
        () => NotificationCubit(
          initializeNotifications: serviceLocator<InitializeNotifications>(),
          showNotification: serviceLocator<ShowNotification>(),
          getFirebaseToken: serviceLocator<GetFirebaseToken>(),
          updateFirebaseToken: serviceLocator<UpdateFirebaseToken>(),
          userCubit: serviceLocator<UserCubit>(),
        ),
      );
  }
}
