import 'package:fpdart/fpdart.dart';
import '../../../../core/error/failure.dart';
import '../../../../core/usecase/usecase.dart';
import '../repositories/video_message_repository.dart';

class GenerateViewUrl implements UseCase<String, String> {
  final VideoMessageRepository repository;

  GenerateViewUrl(this.repository);

  @override
  Future<Either<Failure, String>> call(String messageId) async {
    return await repository.generateViewUrl(messageId);
  }
}
