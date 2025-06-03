import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import 'package:responsive_builder/responsive_builder.dart';

import '../../features/notifications/presentation/screens/notification_settings_dialog.dart';
import '../../features/auth/presentation/cubit/auth_cubit.dart';
import '../constants/constants.dart';
import 'widgets/services_pages_widget.dart';
import '../common/widgets/logo_and_help_widget.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});
  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  late final List<AppServices> _neobellServices;

  @override
  void initState() {
    super.initState();
    _neobellServices = AppServices.values;
  }

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<AuthCubit, AuthState>(
      builder: (context, state) {
        if (state is! AuthAuthenticated) {
          // Handle unauthenticated state
          return const Scaffold(
            body: Center(child: CircularProgressIndicator()),
          );
        }

        final user = state.user;

        return Scaffold(
          floatingActionButton: FloatingActionButton(
            onPressed: () {
              showDialog(
                context: context,
                builder: (context) => NotificationSettingsDialog(),
              );
            },
            child: const Icon(Icons.notifications),
          ),
          body: SafeArea(
            minimum: const EdgeInsets.only(top: 16),
            child: Column(
              children: [
                const LogoAndHelpWidget(logout: true),
                const SizedBox(height: 10),
                Text(
                  'Bem-vindo ${user.name ?? user.email}',
                  style: const TextStyle(
                    fontSize: 25,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 20),
                Text(
                  'Sistema NeoBell',
                  style: TextStyle(
                    fontSize: 18,
                    color: Colors.grey[600],
                    fontWeight: FontWeight.w500,
                  ),
                ),
                const SizedBox(height: 30),
                Expanded(
                  child: Container(
                    margin: const EdgeInsets.symmetric(horizontal: 20),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(15),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.grey.withAlpha(
                            Color.getAlphaFromOpacity(0.5),
                          ),
                          spreadRadius: 5,
                          blurRadius: 7,
                          offset: const Offset(0, 3),
                        ),
                      ],
                    ),
                    child: Padding(
                      padding: const EdgeInsets.all(20.0),
                      child: LayoutBuilder(
                        builder: (context, constraints) {
                          // Responsive grid
                          int crossAxisCount = getValueForScreenType<int>(
                            context: context,
                            mobile: 2,
                            tablet: 3,
                          );

                          return GridView.count(
                            crossAxisCount: crossAxisCount,
                            crossAxisSpacing: 15,
                            mainAxisSpacing: 20,
                            childAspectRatio: 1.0,
                            children: [
                              for (var service in _neobellServices)
                                ServicesPagesWidget(
                                  icon: service.icon,
                                  text: service.name,
                                  onPressed: () {
                                    context.push(service.path);
                                  },
                                ),
                            ],
                          );
                        },
                      ),
                    ),
                  ),
                ),
                const SizedBox(height: 20),
              ],
            ),
          ),
        );
      },
    );
  }
}
