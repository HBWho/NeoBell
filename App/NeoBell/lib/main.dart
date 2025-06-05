import 'package:amplify_authenticator/amplify_authenticator.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:neobell/features/auth/core/auth_init.dart';
import 'package:neobell/features/auth/presentation/screens/login_screen.dart';
import 'package:neobell/features/video_messages/presentation/blocs/video_message_bloc.dart';

import 'core/constants/constants.dart';
import 'core/theme/theme.dart';
import 'features/activity_logs/presentation/blocs/activity_log_bloc.dart';
import 'features/auth/presentation/cubit/auth_cubit.dart';
import 'features/device_management/presentation/blocs/device_bloc.dart';
import 'features/notifications/presentation/cubit/notification_cubit.dart';
import 'features/package_deliveries/presentation/blocs/package_delivery_bloc.dart';
import 'features/user_profile/presentation/cubit/user_profile_cubit.dart';
import 'features/visitor_permissions/presentation/blocs/visitor_permission_bloc.dart';
import 'init_dependencies_imports.dart';
import 'routes.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Firebase.initializeApp(); // Initialize Firebase
  await AuthInit.init(); // Configure Amplify
  await InitDependencies.init(); // Initialize Dependencies
  await serviceLocator<NotificationCubit>()
      .initialize(); // Initialize Notifications
  serviceLocator<AuthCubit>().checkAuthStatus(); // Check Auth Status
  runApp(
    MultiBlocProvider(
      providers: [
        BlocProvider(create: (_) => serviceLocator<AuthCubit>()),
        BlocProvider(create: (_) => serviceLocator<VideoMessageBloc>()),
        BlocProvider(create: (_) => serviceLocator<VisitorPermissionBloc>()),
        BlocProvider(create: (_) => serviceLocator<NotificationCubit>()),
        BlocProvider(create: (_) => serviceLocator<UserProfileCubit>()),
        BlocProvider(create: (_) => serviceLocator<PackageDeliveryBloc>()),
        BlocProvider(create: (_) => serviceLocator<ActivityLogBloc>()),
        BlocProvider(create: (_) => serviceLocator<DeviceBloc>()),
      ],
      child: const MyApp(),
    ),
  );
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});
  @override
  Widget build(BuildContext context) {
    return Authenticator(
      authenticatorBuilder: LoginUIAuthenticator.builder,
      child: MaterialApp.router(
        routerConfig: RouterMain.router,
        debugShowCheckedModeBanner: false,
        title: MainConstants.appName,
        builder: Authenticator.builder(),
        theme: AppTheme.theme,
      ),
    );
  }
}
