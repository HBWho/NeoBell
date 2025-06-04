import 'package:fpdart/fpdart.dart';

import '../../../../core/error/failure.dart';
import '../../../../core/usecase/usecase.dart';
import '../entities/package_delivery.dart';
import '../repositories/package_delivery_repository.dart';

class GetPackageDeliveryDetails implements UseCase<PackageDelivery, String> {
  final PackageDeliveryRepository repository;

  GetPackageDeliveryDetails(this.repository);

  @override
  Future<Either<Failure, PackageDelivery>> call(String orderId) async {
    return await repository.getPackageDeliveryById(orderId);
  }
}
