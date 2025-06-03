import 'package:amplify_authenticator/amplify_authenticator.dart';
import 'package:flutter/material.dart';
import 'package:neobell/core/constants/constants.dart';

class LoginUIAuthenticator {
  static Widget? builder(BuildContext context, AuthenticatorState state) {
    switch (state.currentStep) {
      case AuthenticatorStep.signIn:
        return LoginScaffold(
          body: SignInForm(),
          footer: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Text('Don\'t have an account?'),
              TextButton(
                onPressed: () => state.changeStep(AuthenticatorStep.signUp),
                child: const Text('Sign Up'),
              ),
            ],
          ),
        );
      case AuthenticatorStep.signUp:
        return LoginScaffold(
          body: SignUpForm(),
          footer: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Text('Already have an account?'),
              TextButton(
                onPressed: () => state.changeStep(AuthenticatorStep.signIn),
                child: const Text('Sign In'),
              ),
            ],
          ),
        );
      case AuthenticatorStep.confirmSignUp:
        return LoginScaffold(body: ConfirmSignUpForm());
      case AuthenticatorStep.resetPassword:
        return LoginScaffold(body: ResetPasswordForm());
      case AuthenticatorStep.confirmResetPassword:
        return LoginScaffold(body: const ConfirmResetPasswordForm());
      default:
        // Returning null defaults to the prebuilt authenticator for all other steps
        return null;
    }
  }
}

/// A widget that displays a logo, a body, and an optional footer.
class LoginScaffold extends StatelessWidget {
  const LoginScaffold({super.key, required this.body, this.footer});

  final Widget body;
  final Widget? footer;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: SingleChildScrollView(
          child: Column(
            children: [
              // App logo
              Padding(
                padding: EdgeInsets.only(top: 32),
                child: Center(
                  child: SizedBox(
                    width: double.infinity,
                    height: MediaQuery.of(context).size.height * 0.25,
                    child: Image.asset(AssetsConstants.logo),
                  ),
                ),
              ),
              Container(
                constraints: const BoxConstraints(maxWidth: 600),
                child: body,
              ),
            ],
          ),
        ),
      ),
      persistentFooterButtons: footer != null ? [footer!] : null,
    );
  }
}
