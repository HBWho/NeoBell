import 'package:fpdart/fpdart.dart';

import '../../../../core/error/failure.dart';
import '../entities/nfc_tag.dart';
import '../entities/user_profile.dart';

abstract class UserProfileRepository {
  /// Get the current user's profile
  Future<Either<Failure, UserProfile>> getCurrentProfile();

  /// Update user profile information
  Future<Either<Failure, UserProfile>> updateProfile({required String name});

  /// Register or update device token for push notifications
  Future<Either<Failure, Unit>> updateDeviceToken({
    required String deviceToken,
  });

  /// Register a new NFC tag for the user
  Future<Either<Failure, Unit>> registerNfcTag({
    required String tagId,
    required String friendlyName,
  });

  /// Update an existing NFC tag
  Future<Either<Failure, Unit>> updateNfcTag({
    required String tagId,
    required String friendlyName,
  });

  /// Remove an NFC tag from the user's profile
  Future<Either<Failure, Unit>> removeNfcTag({required String tagId});

  /// Get all registered NFC tags for the user
  Future<Either<Failure, List<NfcTag>>> getNfcTags();
}
