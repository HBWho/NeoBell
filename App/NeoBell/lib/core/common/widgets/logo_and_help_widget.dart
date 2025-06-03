import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

import '../../../features/auth/presentation/cubit/auth_cubit.dart';
import '../../constants/constants.dart';

class LogoAndHelpWidget extends StatelessWidget {
  final bool logout;
  final bool back;
  final double height;
  const LogoAndHelpWidget({
    super.key,
    this.back = true,
    this.logout = false,
    this.height = 0.25,
  });

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: double.infinity,
      height: MediaQuery.of(context).size.height * height,
      child: Stack(
        alignment: Alignment.center,
        children: [
          Image.asset(AssetsConstants.logo),
          if (logout)
            Positioned(
              left: 8,
              top: 1,
              child: IconButton(
                alignment: Alignment.topLeft,
                onPressed: () => context.read<AuthCubit>().signOut(),
                icon: Icon(Icons.logout, size: 30),
              ),
            ),
          if (!logout && back)
            Positioned(
              left: 8,
              top: 1,
              child: IconButton(
                alignment: Alignment.topLeft,
                onPressed: context.pop,
                icon: Icon(Icons.arrow_back, size: 30),
              ),
            ),
        ],
      ),
    );
  }
}
