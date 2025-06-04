import 'package:fpdart/fpdart.dart';

import '../../../../core/error/failure.dart';
import '../entities/package_delivery.dart';
import '../entities/package_delivery_filter.dart';
import '../entities/create_package_delivery.dart';
import '../entities/update_package_delivery.dart';

abstract class PackageDeliveryRepository {
  Future<Either<Failure, List<PackageDelivery>>> getPackageDeliveries({
    PackageDeliveryFilter? filter,
    int? limit,
    String? lastEvaluatedKey,
  });

  Future<Either<Failure, PackageDelivery>> getPackageDeliveryById(
    String orderId,
  );

  Future<Either<Failure, PackageDelivery>> createPackageDelivery(
    CreatePackageDelivery delivery,
  );

  Future<Either<Failure, PackageDelivery>> updatePackageDelivery(
    String orderId,
    UpdatePackageDelivery delivery,
  );

  Future<Either<Failure, void>> deletePackageDelivery(String orderId);
}
