import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:get_it/get_it.dart';
import 'package:http/http.dart' as http;

import 'core/common/cubit/settings/settings_cubit.dart';
import 'core/common/cubit/user/user_cubit.dart';
import 'core/data/api_service.dart';
import 'core/data/repositories/config_repository_impl.dart';
import 'core/data/repositories/local_storage_repository_impl.dart';
import 'core/data/repositories/secure_storage_repository_impl.dart';
import 'core/domain/repositories/config_repository.dart';
import 'core/domain/repositories/local_storage_repository.dart';
import 'core/services/auth_interceptor_service.dart';
import 'features/auth/data/repositories/auth_credentials_repository_impl.dart';
import 'features/auth/data/repositories/auth_repository_impl.dart';
import 'features/auth/data/repositories/auth_repository_mock.dart';
import 'features/auth/data/source/auth_remote_data_source.dart';
import 'features/auth/domain/repositories/auth_credentials_repository.dart';
import 'features/auth/domain/repositories/auth_repository.dart';
import 'features/auth/domain/use_cases/user_get_user.dart';
import 'features/auth/domain/use_cases/user_login.dart';
import 'features/auth/domain/use_cases/user_logout.dart';
import 'features/auth/presentation/blocs/auth_bloc.dart';
import 'features/auth/presentation/cubit/auth_credentials_cubit.dart';
import 'features/notifications/data/datasources/notification_local_data_source.dart';
import 'features/notifications/data/datasources/notification_remote_data_source.dart';
import 'features/notifications/data/repositories/notification_repository_impl.dart';
import 'features/notifications/domain/repositories/notification_repository.dart';
import 'features/notifications/domain/usecases/get_firebase_tolen.dart';
import 'features/notifications/domain/usecases/initialize_notifications.dart';
import 'features/notifications/domain/usecases/show_notification.dart';
import 'features/notifications/domain/usecases/update_firebase_token.dart';
import 'features/notifications/presentation/cubit/notification_cubit.dart';
import 'features/user_actions/log/data/repositories/log_repository_impl.dart';
import 'features/user_actions/log/domain/repositories/log_repository.dart';
import 'features/user_actions/log/domain/use_cases/get_logs.dart';
import 'features/user_actions/log/presentation/blocs/log_bloc.dart';
import 'features/user_actions/user_profiles/data/repositories/user_actions_repository_impl.dart';
import 'features/user_actions/user_profiles/data/source/user_actions_remote_data_source.dart';
import 'features/user_actions/user_profiles/domain/repositories/user_actions_repository.dart';
import 'features/user_actions/user_profiles/domain/use_cases/change_user_roles.dart';
import 'features/user_actions/user_profiles/domain/use_cases/user_get_all_users.dart';
import 'features/user_actions/user_profiles/domain/use_cases/user_get_user_by_user_name.dart';
import 'features/user_actions/user_profiles/domain/use_cases/user_register_user.dart';
import 'features/user_actions/user_profiles/domain/use_cases/user_update_profile.dart';
import 'features/user_actions/user_profiles/presentation/blocs/user_actions_bloc.dart';
import 'features/user_actions/user_profiles/presentation/blocs/user_request_bloc.dart';

part 'init_dependencies.dart';
