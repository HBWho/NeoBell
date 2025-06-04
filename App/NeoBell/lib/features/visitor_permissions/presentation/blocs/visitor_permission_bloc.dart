import 'package:equatable/equatable.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../domain/entities/visitor_permission.dart';
import '../../domain/entities/visitor_permission_with_image.dart';
import '../../domain/use_cases/get_visitor_permissions.dart';
import '../../domain/use_cases/get_visitor_details_with_image.dart';
import '../../domain/use_cases/update_visitor_permission.dart';
import '../../domain/use_cases/delete_visitor_permission.dart';

part 'visitor_permission_event.dart';
part 'visitor_permission_state.dart';

class VisitorPermissionBloc
    extends Bloc<VisitorPermissionEvent, VisitorPermissionState> {
  final GetVisitorPermissions _getVisitorPermissions;
  final GetVisitorDetailsWithImage _getVisitorDetailsWithImage;
  final UpdateVisitorPermission _updateVisitorPermission;
  final DeleteVisitorPermission _deleteVisitorPermission;

  VisitorPermissionBloc({
    required GetVisitorPermissions getVisitorPermissions,
    required GetVisitorDetailsWithImage getVisitorDetailsWithImage,
    required UpdateVisitorPermission updateVisitorPermission,
    required DeleteVisitorPermission deleteVisitorPermission,
  }) : _getVisitorPermissions = getVisitorPermissions,
       _getVisitorDetailsWithImage = getVisitorDetailsWithImage,
       _updateVisitorPermission = updateVisitorPermission,
       _deleteVisitorPermission = deleteVisitorPermission,
       super(VisitorPermissionInitial()) {
    on<LoadVisitorPermissions>(_onLoadVisitorPermissions);
    on<LoadVisitorDetailsWithImage>(_onLoadVisitorDetailsWithImage);
    on<RefreshVisitorDetailsWithImage>(_onRefreshVisitorDetailsWithImage);
    on<UpdateVisitorPermissionEvent>(_onUpdateVisitorPermission);
    on<DeleteVisitorPermissionEvent>(_onDeleteVisitorPermission);
    on<RefreshVisitorPermissions>(_onRefreshVisitorPermissions);
  }

  Future<void> _onLoadVisitorPermissions(
    LoadVisitorPermissions event,
    Emitter<VisitorPermissionState> emit,
  ) async {
    emit(VisitorPermissionLoading());
    final result = await _getVisitorPermissions(
      GetVisitorPermissionsParams(
        limit: event.limit,
        lastEvaluatedKey: event.lastEvaluatedKey,
      ),
    );

    result.fold(
      (failure) => emit(
        VisitorPermissionFailure(
          message: failure.message,
          visitorPermissions: state.visitorPermissions,
          cachedVisitorDetails: state.cachedVisitorDetails,
        ),
      ),
      (visitorPermissions) => emit(
        VisitorPermissionLoaded(
          visitorPermissions: visitorPermissions,
          cachedVisitorDetails: state.cachedVisitorDetails,
          lastEvaluatedKey: event.lastEvaluatedKey,
        ),
      ),
    );
  }

  Future<void> _onLoadVisitorDetailsWithImage(
    LoadVisitorDetailsWithImage event,
    Emitter<VisitorPermissionState> emit,
  ) async {
    final cachedDetails =
        state.cachedVisitorDetails
            .where((details) => details.faceTagId == event.faceTagId)
            .firstOrNull;

    if (cachedDetails != null) {
      emit(
        VisitorPermissionDetailsLoaded(
          currentVisitorDetails: cachedDetails,
          visitorPermissions: state.visitorPermissions,
          cachedVisitorDetails: state.cachedVisitorDetails,
        ),
      );
      return;
    }

    emit(
      VisitorPermissionLoading(
        visitorPermissions: state.visitorPermissions,
        cachedVisitorDetails: state.cachedVisitorDetails,
      ),
    );
    final result = await _getVisitorDetailsWithImage(event.faceTagId);
    result.fold(
      (failure) => emit(
        VisitorPermissionFailure(
          message: failure.message,
          visitorPermissions: state.visitorPermissions,
          cachedVisitorDetails: state.cachedVisitorDetails,
        ),
      ),
      (visitorDetails) {
        final updatedCache = List<VisitorPermissionWithImage>.from(
          state.cachedVisitorDetails,
        )..add(visitorDetails);
        emit(
          VisitorPermissionDetailsLoaded(
            currentVisitorDetails: visitorDetails,
            visitorPermissions: state.visitorPermissions,
            cachedVisitorDetails: updatedCache,
          ),
        );
      },
    );
  }

  Future<void> _onRefreshVisitorDetailsWithImage(
    RefreshVisitorDetailsWithImage event,
    Emitter<VisitorPermissionState> emit,
  ) async {
    final updatedCache =
        state.cachedVisitorDetails
            .where((details) => details.faceTagId != event.faceTagId)
            .toList();
    emit(
      VisitorPermissionLoading(
        visitorPermissions: state.visitorPermissions,
        cachedVisitorDetails: updatedCache,
      ),
    );

    final result = await _getVisitorDetailsWithImage(event.faceTagId);
    result.fold(
      (failure) => emit(
        VisitorPermissionFailure(
          message: failure.message,
          visitorPermissions: state.visitorPermissions,
          cachedVisitorDetails: updatedCache,
        ),
      ),
      (visitorDetails) {
        final newCache = List<VisitorPermissionWithImage>.from(updatedCache)
          ..add(visitorDetails);
        emit(
          VisitorPermissionDetailsLoaded(
            currentVisitorDetails: visitorDetails,
            visitorPermissions: state.visitorPermissions,
            cachedVisitorDetails: newCache,
          ),
        );
      },
    );
  }

  Future<void> _onUpdateVisitorPermission(
    UpdateVisitorPermissionEvent event,
    Emitter<VisitorPermissionState> emit,
  ) async {
    emit(
      VisitorPermissionLoading(
        visitorPermissions: state.visitorPermissions,
        cachedVisitorDetails: state.cachedVisitorDetails,
      ),
    );

    final result = await _updateVisitorPermission(
      UpdateVisitorPermissionParams(
        faceTagId: event.faceTagId,
        visitorName: event.visitorName,
        permissionLevel: event.permissionLevel,
      ),
    );

    result.fold(
      (failure) => emit(
        VisitorPermissionFailure(
          message: failure.message,
          visitorPermissions: state.visitorPermissions,
          cachedVisitorDetails: state.cachedVisitorDetails,
        ),
      ),
      (updatedPermission) {
        final updatedPermissions =
            state.visitorPermissions.map((permission) {
              if (permission.faceTagId == event.faceTagId) {
                return permission.copyWith(
                  visitorName: event.visitorName,
                  permissionLevel: event.permissionLevel,
                  lastUpdatedAt: DateTime.now(),
                );
              }
              return permission;
            }).toList();
        final updatedCache =
            state.cachedVisitorDetails.map((details) {
              if (details.faceTagId == event.faceTagId) {
                return details.copyWith(
                  visitorName: event.visitorName,
                  permissionLevel: event.permissionLevel,
                  lastUpdatedAt: DateTime.now(),
                );
              }
              return details;
            }).toList();
        emit(
          VisitorPermissionOperationSuccess(
            message: 'Visitor permission updated successfully',
            visitorPermissions: updatedPermissions,
            cachedVisitorDetails: updatedCache,
          ),
        );
      },
    );
  }

  Future<void> _onDeleteVisitorPermission(
    DeleteVisitorPermissionEvent event,
    Emitter<VisitorPermissionState> emit,
  ) async {
    emit(
      VisitorPermissionLoading(
        visitorPermissions: state.visitorPermissions,
        cachedVisitorDetails: state.cachedVisitorDetails,
      ),
    );

    final result = await _deleteVisitorPermission(
      DeleteVisitorPermissionParams(faceTagId: event.faceTagId),
    );

    result.fold(
      (failure) => emit(
        VisitorPermissionFailure(
          message: failure.message,
          visitorPermissions: state.visitorPermissions,
          cachedVisitorDetails: state.cachedVisitorDetails,
        ),
      ),
      (_) {
        final updatedPermissions =
            state.visitorPermissions
                .where((permission) => permission.faceTagId != event.faceTagId)
                .toList();
        final updatedCache =
            state.cachedVisitorDetails
                .where((details) => details.faceTagId != event.faceTagId)
                .toList();
        emit(
          VisitorPermissionOperationSuccess(
            message: 'Visitor permission deleted successfully',
            visitorPermissions: updatedPermissions,
            cachedVisitorDetails: updatedCache,
          ),
        );
      },
    );
  }

  Future<void> _onRefreshVisitorPermissions(
    RefreshVisitorPermissions event,
    Emitter<VisitorPermissionState> emit,
  ) async {
    emit(VisitorPermissionLoading());

    final result = await _getVisitorPermissions(GetVisitorPermissionsParams());

    result.fold(
      (failure) => emit(
        VisitorPermissionFailure(
          message: failure.message,
          visitorPermissions: state.visitorPermissions,
          cachedVisitorDetails: state.cachedVisitorDetails,
        ),
      ),
      (visitorPermissions) => emit(
        VisitorPermissionLoaded(
          visitorPermissions: visitorPermissions,
          cachedVisitorDetails: state.cachedVisitorDetails,
        ),
      ),
    );
  }
}
