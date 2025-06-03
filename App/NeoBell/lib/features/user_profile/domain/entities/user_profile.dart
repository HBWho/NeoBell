enum UserRole { owner, resident }

class UserProfile {
  final String id;
  final String email;
  final String name;
  final List<String> nfcTags;

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
    String? deviceToken,
    List<String>? nfcTags,
    UserRole? role,
  }) {
    return UserProfile(
      id: id ?? this.id,
      email: email ?? this.email,
      name: name ?? this.name,
      nfcTags: nfcTags ?? this.nfcTags,
    );
  }
}
