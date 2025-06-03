import 'package:amplify_auth_cognito/amplify_auth_cognito.dart' as amplify;
import '../../domain/entities/auth_user.dart';

/// Maps Cognito user attributes to AuthUser entity
class AuthUserMapper {
  static AuthUser fromCognitoAttributes(
      List<amplify.AuthUserAttribute> attributes) {
    String? id;
    String? email;
    String? name;
    bool isEmailVerified = false;

    for (final attr in attributes) {
      switch (attr.userAttributeKey) {
        case amplify.CognitoUserAttributeKey.sub:
          id = attr.value;
          break;
        case amplify.CognitoUserAttributeKey.email:
          email = attr.value;
          break;
        case amplify.CognitoUserAttributeKey.name:
          name = attr.value;
          break;
        case amplify.CognitoUserAttributeKey.emailVerified:
          isEmailVerified = attr.value.toLowerCase() == 'true';
          break;
        default:
          break;
      }
    }

    if (id == null || email == null) {
      throw Exception('Required user attributes missing');
    }

    return AuthUser(
      id: id,
      email: email,
      name: name,
      isEmailVerified: isEmailVerified,
      lastSignInAt: DateTime.now(),
    );
  }
}
