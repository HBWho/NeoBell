import 'package:fpdart/fpdart.dart';

import '../../../../core/error/failure.dart';
import '../../../../core/usecase/usecase.dart';
import '../repositories/user_profile_repository.dart';

class RegisterNfcTagParams {
  final String tagId;
  final String friendlyName;

  const RegisterNfcTagParams({required this.tagId, required this.friendlyName});
}

class RegisterNfcTag implements UseCase<Unit, RegisterNfcTagParams> {
  final UserProfileRepository repository;

  const RegisterNfcTag(this.repository);

  @override
  Future<Either<Failure, Unit>> call(RegisterNfcTagParams params) async {
    return await repository.registerNfcTag(
      tagId: params.tagId,
      friendlyName: params.friendlyName,
    );
  }
}
