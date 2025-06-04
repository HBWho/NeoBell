import 'package:equatable/equatable.dart';
import 'nfc_tag.dart';

enum UserRole { owner, resident }

class UserProfile extends Equatable {
  final String id;
  final String email;
  final String name;
  final List<NfcTag> nfcTags;

  const UserProfile({
    required this.id,
    required this.email,
    required this.name,
    this.nfcTags = const [],
  });

  UserProfile copyWith({
    String? id,
    String? username,
    String? email,
    String? name,
    List<NfcTag>? nfcTags,
    UserRole? role,
  }) {
    return UserProfile(
      id: id ?? this.id,
      email: email ?? this.email,
      name: name ?? this.name,
      nfcTags: nfcTags ?? this.nfcTags,
    );
  }

  @override
  List<Object?> get props => [id, email, name, nfcTags];
}
