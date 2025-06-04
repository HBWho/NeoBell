import 'package:fpdart/fpdart.dart';

import '../../../../core/error/failure.dart';
import '../../../../core/usecase/usecase.dart';
import '../entities/package_delivery.dart';
import '../entities/create_package_delivery.dart';
import '../repositories/package_delivery_repository.dart';

class CreatePackageDeliveryUseCase
    implements UseCase<PackageDelivery, CreatePackageDelivery> {
  final PackageDeliveryRepository repository;

  CreatePackageDeliveryUseCase(this.repository);

  @override
  Future<Either<Failure, PackageDelivery>> call(
    CreatePackageDelivery params,
  ) async {
    return await repository.createPackageDelivery(params);
  }
}
