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

class RouterMain {
  static final Logger _logger = Logger();
  static final GoRouter router = GoRouter(
    initialLocation: '/',
    navigatorKey: NavigationService.navigatorKey,
    redirect: (context, state) async {
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
          GoRoute(
            path: '/records',
            name: 'records',
            builder: (context, state) {
              return RecordScreen();
            },
          ),
          GoRoute(
            path: '/registeruser',
            name: 'registeruser',
            builder: (context, state) {
              return RegisterUserScreen();
            },
          ),
          // GoRoute(
          //   path: '/warehouses',
          //   name: 'warehouses',
          //   builder: (context, state) => WarehousesScreen(),
          //   routes: [
          //     GoRoute(
          //       path: '/:warehouseId',
          //       name: 'warehouseDetails',
          //       redirect: (context, state) {
          //         final warehouseId = state.pathParameters['warehouseId']!;
          //         if (warehouseId.isEmpty) {
          //           return '/home/warehouses';
          //         }
          //         return null;
          //       },
          //       builder: (context, state) {
          //         final warehouseId = state.pathParameters['warehouseId']!;
          //         return WarehouseDetailsScreen(warehouseId: warehouseId);
          //       },
          //     ),
          //   ],
          // ),
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
