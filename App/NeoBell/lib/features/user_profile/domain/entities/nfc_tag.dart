import 'package:equatable/equatable.dart';

class NfcTag extends Equatable {
  final String tagFriendlyName;
  final String nfcId;

  const NfcTag({required this.tagFriendlyName, required this.nfcId});

  @override
  List<Object?> get props => [tagFriendlyName, nfcId];
}
