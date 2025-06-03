import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:equatable/equatable.dart';

import '../cubit/auth_cubit.dart';

part 'login_event.dart';
part 'login_state.dart';

class LoginBloc extends Bloc<LoginEvent, LoginState> {
  final AuthCubit _authCubit;

  LoginBloc({
    required AuthCubit authCubit,
  })  : _authCubit = authCubit,
        super(LoginInitial()) {
    on<LoginSubmitted>(_onLoginSubmitted);
  }

  Future<void> _onLoginSubmitted(
    LoginSubmitted event,
    Emitter<LoginState> emit,
  ) async {
    emit(LoginLoading());

    // Listen for AuthCubit state changes
    final subscription = _authCubit.stream.listen((authState) {
      if (authState is AuthAuthenticated) {
        emit(LoginSuccess());
      } else if (authState is AuthError) {
        emit(LoginFailure(authState.message));
      }
    });

    // Attempt login via AuthCubit
    await _authCubit.signIn(
      username: event.username,
      password: event.password,
    );

    await subscription.cancel();
  }
}
