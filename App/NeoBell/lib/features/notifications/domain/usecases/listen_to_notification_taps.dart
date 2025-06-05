import 'package:fpdart/fpdart.dart';

import '../../../../core/error/failure.dart';
import '../../../../core/usecase/usecase.dart';
import '../repositories/notification_repository.dart';

class ListenToNotificationTaps
    implements UseCase<Stream<Map<String, dynamic>>, NoParams> {
  final NotificationRepository repository;

  ListenToNotificationTaps(this.repository);

  @override
  Future<Either<Failure, Stream<Map<String, dynamic>>>> call(
    NoParams param,
  ) async {
    return right(repository.onNotificationTap);
  }
}
