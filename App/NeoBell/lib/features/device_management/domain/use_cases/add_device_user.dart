import 'package:fpdart/fpdart.dart';
import '../../../../core/error/failure.dart';
import '../../../../core/usecase/usecase.dart';
import '../repositories/device_repository.dart';

class AddDeviceUser implements UseCase<Unit, AddDeviceUserParams> {
  final DeviceRepository repository;

  AddDeviceUser(this.repository);

  @override
  Future<Either<Failure, Unit>> call(AddDeviceUserParams params) async {
    return await repository.addDeviceUser(params.sbcId, params.userEmail);
  }
}

class AddDeviceUserParams {
  final String sbcId;
  final String userEmail;

  AddDeviceUserParams({required this.sbcId, required this.userEmail});
}
