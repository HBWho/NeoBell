import 'package:fpdart/fpdart.dart';

import '../../../../core/error/failure.dart';
import '../../../../core/usecase/usecase.dart';
import '../entities/package_delivery.dart';
import '../entities/package_delivery_filter.dart';
import '../repositories/package_delivery_repository.dart';

class GetPackageDeliveries
    implements UseCase<List<PackageDelivery>, GetPackageDeliveriesParams> {
  final PackageDeliveryRepository repository;

  GetPackageDeliveries(this.repository);

  @override
  Future<Either<Failure, List<PackageDelivery>>> call(
    GetPackageDeliveriesParams params,
  ) async {
    return await repository.getPackageDeliveries(
      filter: params.filter,
      limit: params.limit,
      lastEvaluatedKey: params.lastEvaluatedKey,
    );
  }
}

class GetPackageDeliveriesParams {
  final PackageDeliveryFilter? filter;
  final int? limit;
  final String? lastEvaluatedKey;

  GetPackageDeliveriesParams({this.filter, this.limit, this.lastEvaluatedKey});
}
