import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:neobell/core/common/widgets/base_screen_widget.dart';
import '../../../../core/utils/show_snackbar.dart';
import '../../../../core/utils/show_confimation_dialog.dart';
import '../../domain/entities/visitor_permission.dart';
import '../blocs/visitor_permission_bloc.dart';
import '../widgets/visitor_permission_item.dart';
import '../widgets/edit_visitor_permission_dialog.dart';
import 'visitor_permission_details_screen.dart';

class VisitorPermissionsScreen extends StatefulWidget {
  const VisitorPermissionsScreen({super.key});

  @override
  State<VisitorPermissionsScreen> createState() =>
      _VisitorPermissionsScreenState();
}

class _VisitorPermissionsScreenState extends State<VisitorPermissionsScreen> {
  @override
  void initState() {
    super.initState();
    final currentState = context.read<VisitorPermissionBloc>().state;
    if (currentState is VisitorPermissionInitial) {
      context.read<VisitorPermissionBloc>().add(LoadVisitorPermissions());
    }
  }

  @override
  Widget build(BuildContext context) {
    return BaseScreenWidget(
      title: 'Visitor Permissions',
      actions: [
        IconButton(
          icon: const Icon(Icons.refresh),
          onPressed: () {
            context.read<VisitorPermissionBloc>().add(
              RefreshVisitorPermissions(),
            );
          },
        ),
      ],
      body: BlocConsumer<VisitorPermissionBloc, VisitorPermissionState>(
        listener: (context, state) {
          if (state is VisitorPermissionFailure) {
            showSnackBar(context, message: state.message, isError: true);
          } else if (state is VisitorPermissionOperationSuccess) {
            showSnackBar(context, message: state.message, isSucess: true);
          }
        },
        builder: (context, state) {
          if (state is VisitorPermissionLoading) {
            return const Center(child: CircularProgressIndicator());
          } else if (state is VisitorPermissionFailure) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.error_outline, size: 64, color: Colors.red),
                  const SizedBox(height: 16),
                  Text(
                    'Error loading visitor permissions',
                    style: TextStyle(fontSize: 18, color: Colors.red[700]),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    state.message,
                    textAlign: TextAlign.center,
                    style: const TextStyle(color: Colors.grey),
                  ),
                  const SizedBox(height: 16),
                  ElevatedButton(
                    onPressed: () {
                      context.read<VisitorPermissionBloc>().add(
                        LoadVisitorPermissions(),
                      );
                    },
                    child: const Text('Retry'),
                  ),
                ],
              ),
            );
          }

          if (state.visitorPermissions.isEmpty) {
            return const Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.people_outline, size: 64, color: Colors.grey),
                  SizedBox(height: 16),
                  Text(
                    'No visitor permissions found',
                    style: TextStyle(fontSize: 18, color: Colors.grey),
                  ),
                  SizedBox(height: 8),
                  Text(
                    'Visitor permissions will appear here when they are detected by the system',
                    textAlign: TextAlign.center,
                    style: TextStyle(color: Colors.grey),
                  ),
                ],
              ),
            );
          }

          return RefreshIndicator(
            onRefresh: () async {
              context.read<VisitorPermissionBloc>().add(
                RefreshVisitorPermissions(),
              );
            },
            child: ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: state.visitorPermissions.length,
              itemBuilder: (context, index) {
                final permission = state.visitorPermissions[index];
                return VisitorPermissionItem(
                  permission: permission,
                  onTap: () => _navigateToDetails(context, permission),
                  onEdit: () => _showEditDialog(context, permission),
                  onDelete: () => _showDeleteConfirmation(context, permission),
                );
              },
            ),
          );
        },
      ),
    );
  }

  void _showEditDialog(BuildContext context, VisitorPermission permission) {
    showDialog(
      context: context,
      builder: (context) => EditVisitorPermissionDialog(permission: permission),
    );
  }

  void _showDeleteConfirmation(
    BuildContext context,
    VisitorPermission permission,
  ) {
    showDialogConfirmation(
      context,
      title: 'Delete Visitor Permission',
      message:
          'Are you sure you want to delete permission for "${permission.visitorName}"? This action cannot be undone.',
      onConfirm: () {
        context.read<VisitorPermissionBloc>().add(
          DeleteVisitorPermissionEvent(faceTagId: permission.faceTagId),
        );
      },
    );
  }

  void _navigateToDetails(BuildContext context, VisitorPermission permission) {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder:
            (context) =>
                VisitorPermissionDetailsScreen(faceTagId: permission.faceTagId),
      ),
    );
  }
}
