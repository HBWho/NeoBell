import 'package:fpdart/fpdart.dart';

import '../../../../core/error/failure.dart';
import '../../../../core/usecase/usecase.dart';
import '../entities/package_delivery.dart';
import '../entities/update_package_delivery.dart';
import '../repositories/package_delivery_repository.dart';

class UpdatePackageDeliveryUseCase
    implements UseCase<PackageDelivery, UpdatePackageDeliveryParams> {
  final PackageDeliveryRepository repository;

  UpdatePackageDeliveryUseCase(this.repository);

  @override
  Future<Either<Failure, PackageDelivery>> call(
    UpdatePackageDeliveryParams params,
  ) async {
    return await repository.updatePackageDelivery(
      params.orderId,
      params.update,
    );
  }
}

class UpdatePackageDeliveryParams {
  final String orderId;
  final UpdatePackageDelivery update;

  UpdatePackageDeliveryParams({required this.orderId, required this.update});
}
