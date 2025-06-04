import 'package:fpdart/fpdart.dart';

import '../../../../core/error/failure.dart';
import '../../../../core/usecase/usecase.dart';
import '../repositories/package_delivery_repository.dart';

class DeletePackageDelivery implements UseCase<Unit, String> {
  final PackageDeliveryRepository repository;

  DeletePackageDelivery(this.repository);

  @override
  Future<Either<Failure, Unit>> call(String orderId) async {
    final result = await repository.deletePackageDelivery(orderId);
    return result.map((_) => unit);
  }
}
