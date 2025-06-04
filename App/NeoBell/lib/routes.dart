import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import 'package:logger/logger.dart';
import 'package:neobell/features/user_profile/presentation/screens/profile_screen.dart';

import 'core/helper/ui_helper.dart';
import 'core/services/navigation_service.dart';
import 'core/screen/home_screen.dart';
import 'features/activities/presentation/screens/all_activities_screen.dart';
import 'features/auth/presentation/cubit/auth_cubit.dart';
import 'features/delivery/presentation/screens/create_delivery_screen.dart';
import 'features/delivery/presentation/screens/delivery_page_screen.dart';
import 'features/members/presentation/screens/registered_members_screen.dart';
import 'features/nfc/presentation/screens/all_registered_nfc_tags_screen.dart';
import 'features/nfc/presentation/screens/nfc_register_screen.dart';
import 'features/visitors/presentation/screens/visitor_notifications_screen.dart';
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
          return const Center(child: CircularProgressIndicator());
        },
      ),
      GoRoute(
        path: '/home',
        name: 'home',
        onExit: (context, state) async {
          final confirmed = await UIHelper.showDialogConfirmation(
            context,
            title: 'Sair',
            message: 'Deseja realmente sair?',
          );
          if (confirmed ?? false) {
            if (context.mounted) context.read<AuthCubit>().signOut();
            return true;
          }
          return false;
        },
        builder: (context, state) {
          // return Center(child: Text('Home Screen Placeholder'));
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
            path: '/all-activities',
            name: 'all-activities',
            builder: (context, state) {
              return AllActivitiesScreen();
            },
          ),
          GoRoute(
            path: '/delivery-page',
            name: 'delivery-page',
            builder: (context, state) {
              return DeliveryPageScreen();
            },
          ),
          GoRoute(
          path: '/delivery-records',
          name: 'delivery-records',
          builder: (context, state) => const AllDeliveryRecordsScreen(),
          ),
          GoRoute(
            path: '/visitor-notifications',
            name: 'visitor-notifications',
            builder: (context, state) {
              return VisitorNotificationsScreen();
            },
          ),
            GoRoute(
            path: '/visitor-notification-detail',
            name: 'visitor-notification-detail',
            builder: (context, state) {
              final notification = state.extra! as Map<String, String>;
              return VisitorNotificationDetailScreen(notification: notification);
            },
          ),
          GoRoute(
            path: '/registered-members',
            name: 'registered-members',
            builder: (context, state) {
              return RegisteredMembersScreen();
            },
          ),
          GoRoute(
            path: '/nfc-register',
            name: 'nfc-register',
            builder: (context, state) {
              return NfcRegisterScreen();
            },
            routes: [
              // Sub-route for all registered NFC tags
              GoRoute(
                path: '/all-tags',
                name: 'all-nfc-tags',
                builder: (context, state) {
                  return AllRegisteredNfcTagsScreen();
                },
              ),
            ],
          ),
          GoRoute(
            path: '/create-delivery',
            name: 'create-delivery',
            builder: (context, state) {
              return CreateDeliveryScreen();
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
