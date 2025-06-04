import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import 'package:logger/logger.dart';
import 'package:neobell/core/screen/splash_screen.dart';
import 'package:neobell/features/user_profile/presentation/screens/profile_screen.dart';
import 'package:neobell/features/video_messages/presentation/blocs/video_message_bloc.dart';
import 'package:neobell/features/video_messages/presentation/blocs/video_message_state.dart';
import 'package:neobell/features/video_messages/presentation/screens/video_messages_screen.dart';
import 'package:neobell/features/video_messages/presentation/screens/watch_video_screen.dart';

import 'core/helper/ui_helper.dart';
import 'core/services/navigation_service.dart';
import 'core/screen/home_screen.dart';
import 'features/activity_logs/presentation/screens/activity_logs_screen.dart';
import 'features/auth/presentation/cubit/auth_cubit.dart';
import 'features/members/presentation/screens/registered_members_screen.dart';
import 'features/nfc/presentation/screens/nfc_screen.dart';
import 'features/visitor_permissions/presentation/screens/visitor_permissions_screen.dart';
import 'init_dependencies_imports.dart';

class RouterMain {
  static final Logger _logger = Logger();
  static final AuthCubit _authCubit = serviceLocator<AuthCubit>();
  static final GoRouter router = GoRouter(
    initialLocation: '/',
    navigatorKey: NavigationService.navigatorKey,
    refreshListenable: GoRouterRefreshStream(_authCubit.stream),
    redirect: (context, state) async {
      final authState = context.read<AuthCubit>().state;
      final String currentPath = state.matchedLocation;
      _logger.i(
        'Router redirect: Current AuthState: $authState, Path: $currentPath',
      );

      // Handle redirection based on authentication state
      // If the user is not authenticated, redirect to the splash or login page
      if (authState is AuthInitial || authState is AuthInProgress) {
        return currentPath == '/splash' ? null : '/splash';
      }

      // If the user is authenticated, redirect to home if on splash or login page
      // Otherwise, allow access to the current path
      final isLoggedIn = authState is AuthAuthenticated;
      if (isLoggedIn) {
        if (currentPath == '/splash' || currentPath == '/') {
          _logger.i('User logged in. Redirecting from $currentPath to /home');
          return '/home';
        }
        return null;
      } else {
        if (currentPath != '/') {
          _logger.i(
            'User NOT logged in. Redirecting from $currentPath to / (login)',
          );
          return '/';
        }
        return null;
      }
    },
    routes: [
      GoRoute(
        path: '/',
        name: 'login',
        builder: (context, state) {
          return Center(
            child: ElevatedButton(
              onPressed: () => context.goNamed('/home'),
              child: Text('If you didn\'t get redirected, please click here'),
            ),
          );
        },
      ),
      GoRoute(
        path: '/splash',
        name: 'splash',
        builder: (context, state) {
          return SplashScreen();
        },
      ),
      GoRoute(
        path: '/home',
        name: 'home',
        onExit: (context, state) async {
          final confirmed = await UIHelper.showDialogConfirmation(
            context,
            title: 'Logout',
            message: 'Are you sure you want to log out?',
          );
          if (confirmed ?? false) {
            if (context.mounted) context.read<AuthCubit>().signOut();
            return true;
          }
          return false;
        },
        builder: (context, state) {
          return HomeScreen();
        },
        routes: [
          GoRoute(
            path: '/profile',
            name: 'profile',
            builder: (context, state) {
              return ProfileScreen();
            },
          ),
          GoRoute(
            path: '/activity-logs',
            name: 'activity-logs',
            builder: (context, state) {
              return ActivityLogsScreen();
            },
          ),
          GoRoute(
            path: '/delivery-page',
            name: 'delivery-page',
            builder: (context, state) {
              return Container();
            },
          ),
          GoRoute(
            path: '/visitor-permissions',
            name: 'visitor-permissions',
            builder: (context, state) {
              return VisitorPermissionsScreen();
            },
          ),
          GoRoute(
            path: '/video-messages',
            name: 'video-messages',
            builder: (context, state) {
              return VideoMessagesScreen();
            },
            routes: [
              GoRoute(
                path: '/:id/watch-video',
                name: 'watch-video',
                redirect: (context, state) {
                  // Verify if everything is ok to access the video screen
                  final videoMessageBloc = context.read<VideoMessageBloc>();
                  final currentState = videoMessageBloc.state;
                  final messageId = state.pathParameters['id'];
                  // We check if the VideoMessageBloc is in a state that allows access to the video screen
                  // and if the messageId matches the one in the state
                  if (currentState is ViewUrlGenerated &&
                      currentState.messageId == messageId) {
                    return null;
                  }
                  return '/home/video-messages';
                },
                builder: (context, state) {
                  final messageId = state.pathParameters['id']!;
                  return WatchVideoScreen(messageId: messageId);
                },
              ),
            ],
          ),
          GoRoute(
            path: '/registered-members',
            name: 'registered-members',
            builder: (context, state) {
              return RegisteredMembersScreen();
            },
          ),
          GoRoute(
            path: '/nfc',
            name: 'nfc',
            builder: (context, state) {
              return NfcScreen();
            },
          ),
          GoRoute(
            path: '/create-delivery',
            name: 'create-delivery',
            builder: (context, state) {
              return Container();
            },
          ),
        ],
      ),
    ],
  );
}

class GoRouterRefreshStream extends ChangeNotifier {
  late final StreamSubscription<dynamic> _subscription;

  GoRouterRefreshStream(Stream<dynamic> stream) {
    notifyListeners();
    _subscription = stream.asBroadcastStream().listen(
      (dynamic _) => notifyListeners(),
    );
  }

  @override
  void dispose() {
    _subscription.cancel();
    super.dispose();
  }
}
