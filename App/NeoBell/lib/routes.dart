import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import 'package:logger/logger.dart';

import 'core/helper/ui_helper.dart';
import 'core/services/navigation_service.dart';
import 'features/auth/presentation/blocs/auth_bloc.dart';
import 'core/common/cubit/user/user_cubit.dart';
import 'features/user_actions/user_profiles/presentation/screen/change_profile_screen.dart';
import 'features/user_actions/log/presentation/screens/record_screen.dart';
import 'core/screen/home_screen.dart';
import 'features/auth/presentation/screen/login_screen.dart';
import 'features/user_actions/user_profiles/presentation/screen/register_user_screen.dart';

// Import placeholder screens (we'll create these next)
import 'features/activities/presentation/screens/all_activities_screen.dart';
import 'features/delivery/presentation/screens/delivery_page_screen.dart';
import 'features/visitors/presentation/screens/visitor_notifications_screen.dart';
import 'features/members/presentation/screens/registered_members_screen.dart';
import 'features/nfc/presentation/screens/nfc_register_screen.dart';
import 'features/nfc/presentation/screens/all_registered_nfc_tags_screen.dart';
import 'features/delivery/presentation/screens/create_delivery_screen.dart';

class RouterMain {
  static final Logger _logger = Logger();
  static final GoRouter router = GoRouter(
    initialLocation: '/',
    navigatorKey: NavigationService.navigatorKey,
    redirect: (context, state) async {
      // Authentication logic (commented out for now)
      // final isLoggedIn = context.read<UserCubit>().state is UserLoggedIn;
      // final isLoggingIn = state.path == '/';
      // if (!isLoggedIn && !isLoggingIn) {
      //   _logger.i('No user logged in, redirecting to login');
      //   return '/';
      // }
      // return null;
    },
    routes: [
      GoRoute(
        path: '/',
        name: 'login',
        builder: (context, state) {
          return LoginScreen();
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
            if (context.mounted) context.read<AuthBloc>().add(AuthLogout());
            return true;
          }
          return false;
        },
        builder: (context, state) {
          return HomeScreen();
        },
        routes: [
          // NeoBell 6 main screens
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
            path: '/visitor-notifications',
            name: 'visitor-notifications',
            builder: (context, state) {
              return VisitorNotificationsScreen();
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
          // Keep existing routes if needed
          GoRoute(
            path: '/changeprofile',
            name: 'changeProfile',
            builder: (context, state) {
              final targetUser = state.uri.queryParameters['targetUser'];
              return ChangeProfileScreen(
                targetUserName: targetUser,
              );
            },
          ),
        ],
      ),
    ],
  );
}
