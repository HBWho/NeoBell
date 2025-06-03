import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:get_it/get_it.dart';
import 'package:http/http.dart' as http;

import 'core/data/api_service.dart';
import 'core/domain/repositories/local_storage_repository.dart';
import 'core/domain/repositories/token_repository.dart';
import 'core/data/repositories/local_storage_repository_impl.dart';
import 'core/data/repositories/secure_storage_repository_impl.dart';
import 'core/services/auth_interceptor_service.dart';
import 'core/services/token_manager.dart';

import 'features/auth/data/repositories/cognito_auth_repository.dart';
import 'features/auth/data/repositories/token_repository_impl.dart';
import 'features/auth/domain/repositories/auth_repository.dart';
import 'features/auth/domain/usecases/check_auth_status.dart';
import 'features/auth/domain/usecases/sign_in.dart';
import 'features/auth/domain/usecases/sign_out.dart';
import 'features/auth/presentation/cubit/auth_cubit.dart';

import 'features/notifications/data/datasources/notification_local_data_source.dart';
import 'features/notifications/data/datasources/notification_remote_data_source.dart';
import 'features/notifications/data/repositories/notification_repository_impl.dart';
import 'features/notifications/domain/repositories/notification_repository.dart';
import 'features/notifications/domain/usecases/get_firebase_tolen.dart';
import 'features/notifications/domain/usecases/initialize_notifications.dart';
import 'features/notifications/domain/usecases/show_notification.dart';
import 'features/notifications/presentation/cubit/notification_cubit.dart';

import 'features/user_profile/data/datasources/user_profile_remote_data_source.dart';
import 'features/user_profile/data/repositories/user_profile_repository_impl.dart';
import 'features/user_profile/domain/repositories/user_profile_repository.dart';
import 'features/user_profile/domain/use_cases/get_current_profile.dart';
import 'features/user_profile/domain/use_cases/get_nfc_tags.dart';
import 'features/user_profile/domain/use_cases/register_nfc_tag.dart';
import 'features/user_profile/domain/use_cases/remove_nfc_tag.dart';
import 'features/user_profile/domain/use_cases/update_device_token.dart';
import 'features/user_profile/domain/use_cases/update_nfc_tag.dart';
import 'features/user_profile/domain/use_cases/update_profile.dart';
import 'features/user_profile/presentation/cubit/user_profile_cubit.dart';

part 'init_dependencies.dart';
