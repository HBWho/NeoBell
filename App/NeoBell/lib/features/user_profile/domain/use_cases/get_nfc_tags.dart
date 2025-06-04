import 'package:fpdart/fpdart.dart';

import '../../../../core/error/failure.dart';
import '../../../../core/usecase/usecase.dart';
import '../entities/nfc_tag.dart';
import '../repositories/user_profile_repository.dart';

class GetNfcTags implements UseCase<List<NfcTag>, NoParams> {
  final UserProfileRepository repository;

  const GetNfcTags(this.repository);

  @override
  Future<Either<Failure, List<NfcTag>>> call(NoParams params) async {
    return await repository.getNfcTags();
  }
}
