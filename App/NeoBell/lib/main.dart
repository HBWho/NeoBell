import 'package:amplify_auth_cognito/amplify_auth_cognito.dart';
import 'package:amplify_authenticator/amplify_authenticator.dart';
import 'package:amplify_flutter/amplify_flutter.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:neobell/features/auth/presentation/screens/login_screen.dart';

import 'amplifyconfiguration.dart';
import 'core/constants/constants.dart';
import 'core/theme/theme.dart';
import 'features/auth/presentation/cubit/auth_cubit.dart';
import 'features/notifications/presentation/cubit/notification_cubit.dart';
import 'features/user_profile/presentation/cubit/user_profile_cubit.dart';
import 'init_dependencies_imports.dart';
import 'routes.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Firebase.initializeApp(); // Initialize Firebase
  await _configureAmplify(); // Configure Amplify
  await InitDependencies.init(); // Initialize Dependencies
  await serviceLocator<NotificationCubit>()
      .initialize(); // Initialize Notifications
  serviceLocator<AuthCubit>().checkAuthStatus(); // Check Auth Status
  runApp(
    MultiBlocProvider(
      providers: [
        BlocProvider(create: (_) => serviceLocator<AuthCubit>()),
        BlocProvider(create: (_) => serviceLocator<NotificationCubit>()),
        BlocProvider(create: (_) => serviceLocator<UserProfileCubit>()),
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

Future<void> _configureAmplify() async {
  try {
    final auth = AmplifyAuthCognito();
    await Amplify.addPlugin(auth);

    await Amplify.configure(amplifyconfig);
  } on Exception catch (e) {
    safePrint('An error occurred configuring Amplify: $e');
  }
}
