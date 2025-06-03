import 'package:fpdart/fpdart.dart';

import '../../../../core/error/failure.dart';
import '../../../../core/usecase/usecase.dart';
import '../repositories/user_profile_repository.dart';

class UpdateNfcTagParams {
  final String tagId;
  final String friendlyName;

  const UpdateNfcTagParams({
    required this.tagId,
    required this.friendlyName,
  });
}

class UpdateNfcTag implements UseCase<Unit, UpdateNfcTagParams> {
  final UserProfileRepository repository;

  const UpdateNfcTag(this.repository);

  @override
  Future<Either<Failure, Unit>> call(UpdateNfcTagParams params) async {
    return await repository.updateNfcTag(
      tagId: params.tagId,
      friendlyName: params.friendlyName,
    );
  }
}
