/// This file contains the Amplify configuration for your Flutter application.
/// It includes the necessary settings for AWS Cognito authentication.
const String amplifyconfig = '''{
    "UserAgent": "aws-amplify-cli/2.0",
    "Version": "1.0",
    "auth": {
        "plugins": {
            "awsCognitoAuthPlugin": {
                "UserAgent": "aws-amplify-flutter/1.0.0",
                "Version": "1.0.0",
                "CognitoUserPool": {
                    "Default": {
                        "PoolId": "us-east-1_7s5Ur8SOU",
                        "AppClientId": "4nfjiuvgnko1nvjtbbjlsoqht0",
                        "Region": "us-east-1"
                    }
                },
                "Auth": {
                    "Default": {
                        "authenticationFlowType": "USER_SRP_AUTH",
                        "usernameAttributes": ["email"],
                        "signupAttributes": ["email", "name"],
                        "passwordProtectionSettings": {
                            "passwordPolicyMinLength": 8,
                            "passwordPolicyCharacters": [
                                "REQUIRES_LOWERCASE",
                                "REQUIRES_UPPERCASE",
                                "REQUIRES_NUMBERS",
                                "REQUIRES_SYMBOLS"
                            ]
                        }
                    }
                }
            }
        }
    }
}''';
