import 'package:fpdart/fpdart.dart';

import '../../../../core/error/failure.dart';
import '../../../../core/error/server_exception.dart';
import '../../domain/entities/user_profile.dart';
import '../../domain/repositories/user_profile_repository.dart';
import '../datasources/user_profile_remote_data_source.dart';

class UserProfileRepositoryImpl implements UserProfileRepository {
  final UserProfileRemoteDataSource remoteDataSource;

  UserProfileRepositoryImpl(this.remoteDataSource);

  @override
  Future<Either<Failure, UserProfile>> getCurrentProfile() async {
    try {
      final profile = await remoteDataSource.getCurrentProfile();
      return Right(profile);
    } on ServerException catch (e) {
      return Left(Failure(e.message));
    }
  }

  @override
  Future<Either<Failure, UserProfile>> updateProfile({
    required String name,
    required String email,
  }) async {
    try {
      final profile = await remoteDataSource.updateProfile(
        name: name,
        email: email,
      );
      return Right(profile);
    } on ServerException catch (e) {
      return Left(Failure(e.message));
    }
  }

  @override
  Future<Either<Failure, Unit>> updateDeviceToken({
    required String deviceToken,
  }) async {
    try {
      await remoteDataSource.updateDeviceToken(deviceToken: deviceToken);
      return const Right(unit);
    } on ServerException catch (e) {
      return Left(Failure(e.message));
    }
  }

  @override
  Future<Either<Failure, Unit>> registerNfcTag({
    required String tagId,
  }) async {
    try {
      await remoteDataSource.registerNfcTag(tagId: tagId);
      return const Right(unit);
    } on ServerException catch (e) {
      return Left(Failure(e.message));
    }
  }

  @override
  Future<Either<Failure, Unit>> updateNfcTag({
    required String tagId,
    required String friendlyName,
  }) async {
    try {
      await remoteDataSource.updateNfcTag(
        tagId: tagId,
        friendlyName: friendlyName,
      );
      return const Right(unit);
    } on ServerException catch (e) {
      return Left(Failure(e.message));
    }
  }

  @override
  Future<Either<Failure, Unit>> removeNfcTag({
    required String tagId,
  }) async {
    try {
      await remoteDataSource.removeNfcTag(tagId: tagId);
      return const Right(unit);
    } on ServerException catch (e) {
      return Left(Failure(e.message));
    }
  }

  @override
  Future<Either<Failure, List<String>>> getNfcTags() async {
    try {
      final tags = await remoteDataSource.getNfcTags();
      return Right(tags);
    } on ServerException catch (e) {
      return Left(Failure(e.message));
    }
  }
}
