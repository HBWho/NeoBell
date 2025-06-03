import 'package:fpdart/fpdart.dart';

import '../../../../core/error/failure.dart';
import '../../../../core/usecase/usecase.dart';
import '../repositories/user_profile_repository.dart';

class RemoveNfcTagParams {
  final String tagId;

  const RemoveNfcTagParams({required this.tagId});
}

class RemoveNfcTag implements UseCase<Unit, RemoveNfcTagParams> {
  final UserProfileRepository repository;

  const RemoveNfcTag(this.repository);

  @override
  Future<Either<Failure, Unit>> call(RemoveNfcTagParams params) async {
    return await repository.removeNfcTag(
      tagId: params.tagId,
    );
  }
}
