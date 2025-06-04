import '../../domain/entities/user_profile.dart';
import 'nfc_tag_model.dart';

class UserProfileModel extends UserProfile {
  const UserProfileModel({
    required super.id,
    required super.email,
    required super.name,
    super.nfcTags = const [],
  });

  factory UserProfileModel.fromJson(Map<String, dynamic> json) {
    return UserProfileModel(
      id: json['user_id'] as String,
      email: json['email'] as String,
      name: json['name'] as String,
      nfcTags:
          (json['tags'] as List<dynamic>?)
              ?.map((e) => NfcTagModel.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const [],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'email': email,
      'name': name,
      'tags':
          nfcTags
              .map(
                (tag) => {
                  'tag_friendly_name': tag.tagFriendlyName,
                  'nfc_id': tag.nfcId,
                },
              )
              .toList(),
    };
  }
}
