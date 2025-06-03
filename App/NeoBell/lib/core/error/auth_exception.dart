class AuthException implements Exception {
  final bool isLoggedIn;
  final String message;

  AuthException({
    this.isLoggedIn = false,
    String? message,
  }) : message = message ??
            (isLoggedIn ? 'Login Realizado com Sucesso' : 'Usuário não Logado');
}
