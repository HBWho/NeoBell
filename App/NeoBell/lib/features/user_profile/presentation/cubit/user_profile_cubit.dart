import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:equatable/equatable.dart';

import '../../../../core/usecase/usecase.dart';
import '../../domain/entities/user_profile.dart';
import '../../domain/use_cases/get_current_profile.dart';
import '../../domain/use_cases/update_profile.dart';
import '../../domain/use_cases/get_nfc_tags.dart';
import '../../domain/use_cases/register_nfc_tag.dart';
import '../../domain/use_cases/remove_nfc_tag.dart';
import '../../domain/use_cases/update_nfc_tag.dart';
import '../../domain/use_cases/update_device_token.dart';

part 'user_profile_state.dart';

class UserProfileCubit extends Cubit<UserProfileState> {
  final GetCurrentProfile _getCurrentProfile;
  final UpdateProfile _updateProfile;
  final GetNfcTags _getNfcTags;
  final RegisterNfcTag _registerNfcTag;
  final RemoveNfcTag _removeNfcTag;
  final UpdateNfcTag _updateNfcTag;
  final UpdateDeviceToken _updateDeviceToken;

  UserProfileCubit({
    required GetCurrentProfile getCurrentProfile,
    required UpdateProfile updateProfile,
    required GetNfcTags getNfcTags,
    required RegisterNfcTag registerNfcTag,
    required RemoveNfcTag removeNfcTag,
    required UpdateNfcTag updateNfcTag,
    required UpdateDeviceToken updateDeviceToken,
  })  : _getCurrentProfile = getCurrentProfile,
        _updateProfile = updateProfile,
        _getNfcTags = getNfcTags,
        _registerNfcTag = registerNfcTag,
        _removeNfcTag = removeNfcTag,
        _updateNfcTag = updateNfcTag,
        _updateDeviceToken = updateDeviceToken,
        super(const UserProfileInitial());

  Future<void> loadProfile() async {
    emit(const UserProfileLoading());
    final result = await _getCurrentProfile(const NoParams());
    result.fold(
      (failure) => emit(UserProfileError(failure.message)),
      (profile) => emit(UserProfileLoaded(profile)),
    );
  }

  Future<void> updateProfile({
    required String name,
    required String email,
  }) async {
    emit(const UserProfileLoading());
    final result = await _updateProfile(
      UpdateProfileParams(
        name: name,
        email: email,
      ),
    );
    result.fold(
      (failure) => emit(UserProfileError(failure.message)),
      (profile) => emit(UserProfileLoaded(profile)),
    );
  }

  Future<void> updateDeviceToken(String token) async {
    final result = await _updateDeviceToken(
      UpdateDeviceTokenParams(deviceToken: token),
    );
    result.fold(
      (failure) => emit(UserProfileError(failure.message)),
      (_) {
        // Maintain current state but update the token
        if (state is UserProfileLoaded) {
          final currentProfile = (state as UserProfileLoaded).profile;
          emit(UserProfileLoaded(
            currentProfile.copyWith(deviceToken: token),
          ));
        }
      },
    );
  }

  Future<void> loadNfcTags() async {
    final result = await _getNfcTags(const NoParams());
    result.fold(
      (failure) => emit(UserProfileError(failure.message)),
      (tags) {
        if (state is UserProfileLoaded) {
          final currentProfile = (state as UserProfileLoaded).profile;
          emit(UserProfileLoaded(
            currentProfile.copyWith(nfcTags: tags),
          ));
        }
      },
    );
  }

  Future<void> registerNfcTag(String tagId) async {
    final result = await _registerNfcTag(RegisterNfcTagParams(tagId: tagId));
    result.fold(
      (failure) => emit(UserProfileError(failure.message)),
      (_) => loadNfcTags(), // Reload tags after successful registration
    );
  }

  Future<void> updateNfcTag({
    required String tagId,
    required String friendlyName,
  }) async {
    final result = await _updateNfcTag(
      UpdateNfcTagParams(
        tagId: tagId,
        friendlyName: friendlyName,
      ),
    );
    result.fold(
      (failure) => emit(UserProfileError(failure.message)),
      (_) => loadNfcTags(), // Reload tags after successful update
    );
  }

  Future<void> removeNfcTag(String tagId) async {
    final result = await _removeNfcTag(RemoveNfcTagParams(tagId: tagId));
    result.fold(
      (failure) => emit(UserProfileError(failure.message)),
      (_) => loadNfcTags(), // Reload tags after successful removal
    );
  }
}
