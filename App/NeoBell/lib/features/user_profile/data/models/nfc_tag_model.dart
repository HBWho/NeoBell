import '../../domain/entities/nfc_tag.dart';

class NfcTagModel extends NfcTag {
  const NfcTagModel({required super.tagFriendlyName, required super.nfcId});

  factory NfcTagModel.fromJson(Map<String, dynamic> json) {
    return NfcTagModel(
      tagFriendlyName: json['tag_friendly_name'] as String? ?? '',
      nfcId: json['nfc_id'] as String,
    );
  }

  Map<String, dynamic> toJson() {
    return {'tag_friendly_name': tagFriendlyName, 'nfc_id': nfcId};
  }
}
