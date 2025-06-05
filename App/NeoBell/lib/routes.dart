import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import 'package:logger/logger.dart';
import 'package:neobell/core/screen/splash_screen.dart';
import 'package:neobell/features/device_management/presentation/screens/devices_screen.dart'
    show DevicesScreen;
import 'package:neobell/features/user_profile/presentation/screens/profile_screen.dart';
import 'package:neobell/features/video_messages/presentation/screens/video_messages_screen.dart';
import 'package:neobell/features/video_messages/presentation/screens/watch_video_screen.dart';

import 'core/helper/ui_helper.dart';
import 'core/services/navigation_service.dart';
import 'core/screen/home_screen.dart';
import 'features/activity_logs/presentation/screens/activity_logs_screen.dart';
import 'features/auth/presentation/cubit/auth_cubit.dart';
import 'features/device_management/presentation/screens/device_details_screen.dart';
import 'features/user_profile/presentation/screens/nfc_screen.dart';
import 'features/package_deliveries/presentation/screens/package_deliveries_screen.dart';
import 'features/package_deliveries/presentation/screens/package_delivery_details_screen.dart';
import 'features/visitor_permissions/presentation/screens/visitor_permission_details_screen.dart';
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
              return PackageDeliveriesScreen();
            },
            routes: [
              GoRoute(
                path: '/:orderId',
                name: 'package-delivery-details',
                redirect: (context, state) {
                  final orderId = state.pathParameters['orderId'];
                  if (orderId != null && orderId.isNotEmpty) {
                    return null;
                  }
                  return '/home/delivery-page';
                },
                builder: (context, state) {
                  final orderId = state.pathParameters['orderId']!;
                  return PackageDeliveryDetailsScreen(orderId: orderId);
                },
              ),
            ],
          ),
          GoRoute(
            path: '/visitor-permissions',
            name: 'visitor-permissions',
            builder: (context, state) {
              return VisitorPermissionsScreen();
            },
            routes: [
              GoRoute(
                path: '/:id',
                name: 'visitor-permission-details',
                redirect: (context, state) {
                  final id = state.pathParameters['id'];
                  if (id != null && id.isNotEmpty) {
                    return null;
                  }
                  return '/home/visitor-permissions';
                },
                builder: (context, state) {
                  final id = state.pathParameters['id']!;
                  return VisitorPermissionDetailsScreen(faceTagId: id);
                },
              ),
            ],
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
                  final messageId = state.pathParameters['id'];
                  if (messageId != null && messageId.isNotEmpty) {
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
            path: '/devices-management',
            name: 'devices-management',
            builder: (context, state) {
              return DevicesScreen();
            },
            routes: [
              GoRoute(
                path: '/:sbcId',
                name: 'device-details',
                builder: (context, state) {
                  final sbcId = state.pathParameters['sbcId']!;
                  return DeviceDetailsScreen(sbcId: sbcId);
                },
              ),
            ],
          ),
          GoRoute(
            path: '/nfc',
            name: 'nfc',
            builder: (context, state) {
              return NfcScreen();
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
