import 'package:fpdart/fpdart.dart';
import '../../../../core/error/failure.dart';
import '../../../../core/usecase/usecase.dart';
import '../repositories/video_message_repository.dart';

class DeleteMessage implements UseCase<void, String> {
  final VideoMessageRepository repository;

  DeleteMessage(this.repository);

  @override
  Future<Either<Failure, void>> call(String messageId) async {
    return await repository.deleteMessage(messageId);
  }
}
