import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:intl/intl.dart';
import 'package:neobell/core/common/widgets/base_screen_widget.dart';
import '../../../../core/utils/show_snackbar.dart';
import '../../../../core/utils/show_confimation_dialog.dart';
import '../../domain/entities/visitor_permission.dart';
import '../../domain/entities/visitor_permission_with_image.dart';
import '../blocs/visitor_permission_bloc.dart';
import '../widgets/edit_visitor_permission_dialog.dart';

class VisitorPermissionDetailsScreen extends StatefulWidget {
  final String faceTagId;
  final String? heroTag; // Para animação de transição

  const VisitorPermissionDetailsScreen({
    super.key,
    required this.faceTagId,
    this.heroTag,
  });

  @override
  State<VisitorPermissionDetailsScreen> createState() =>
      _VisitorPermissionDetailsScreenState();
}

class _VisitorPermissionDetailsScreenState
    extends State<VisitorPermissionDetailsScreen> {
  @override
  void initState() {
    super.initState();
    context.read<VisitorPermissionBloc>().add(
      LoadVisitorDetailsWithImage(faceTagId: widget.faceTagId),
    );
  }

  @override
  Widget build(BuildContext context) {
    return BaseScreenWidget(
      title: 'Visitor Details',
      actions: [
        IconButton(
          onPressed: () {
            context.read<VisitorPermissionBloc>().add(
              RefreshVisitorDetailsWithImage(faceTagId: widget.faceTagId),
            );
          },
          icon: const Icon(Icons.refresh),
          tooltip: 'Refresh',
        ),
      ],
      body: BlocConsumer<VisitorPermissionBloc, VisitorPermissionState>(
        listener: (context, state) {
          if (state is VisitorPermissionFailure) {
            showSnackBar(context, message: state.message, isError: true);
          } else if (state is VisitorPermissionOperationSuccess) {
            showSnackBar(context, message: state.message, isSucess: true);
            // Recarregar os dados após uma operação bem-sucedida
            context.read<VisitorPermissionBloc>().add(
              LoadVisitorDetailsWithImage(faceTagId: widget.faceTagId),
            );
          }
        },
        builder: (context, state) {
          if (state is VisitorPermissionLoading) {
            return const Center(child: CircularProgressIndicator());
          }

          if (state is VisitorPermissionDetailsLoaded) {
            return _buildDetailsView(context, state.currentVisitorDetails);
          }

          if (state is VisitorPermissionFailure) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.error_outline, size: 64, color: Colors.red),
                  const SizedBox(height: 16),
                  Text(
                    'Error loading visitor details',
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
                        LoadVisitorDetailsWithImage(
                          faceTagId: widget.faceTagId,
                        ),
                      );
                    },
                    child: const Text('Retry'),
                  ),
                ],
              ),
            );
          }

          // Estado inicial - mostra loading
          return const Center(child: CircularProgressIndicator());
        },
      ),
    );
  }

  Widget _buildDetailsView(
    BuildContext context,
    VisitorPermissionWithImage visitorDetails,
  ) {
    final theme = Theme.of(context);
    final dateFormat = DateFormat('MMM dd, yyyy HH:mm');

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Imagem do visitante
          Center(
            child: Hero(
              tag:
                  widget.heroTag ?? 'visitor_image_${visitorDetails.faceTagId}',
              child: Container(
                width: 200,
                height: 200,
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(16),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withOpacity(0.1),
                      blurRadius: 10,
                      offset: const Offset(0, 4),
                    ),
                  ],
                ),
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(16),
                  child: Image.network(
                    visitorDetails.imageUrl,
                    fit: BoxFit.cover,
                    loadingBuilder: (context, child, loadingProgress) {
                      if (loadingProgress == null) return child;
                      return Container(
                        color: Colors.grey[200],
                        child: const Center(child: CircularProgressIndicator()),
                      );
                    },
                    errorBuilder:
                        (context, error, stackTrace) => Container(
                          color: Colors.grey[200],
                          child: const Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Icon(Icons.person, size: 48, color: Colors.grey),
                              SizedBox(height: 8),
                              Text(
                                'Image not available',
                                style: TextStyle(color: Colors.grey),
                              ),
                            ],
                          ),
                        ),
                  ),
                ),
              ),
            ),
          ),
          const SizedBox(height: 24),

          // Informações do visitante
          Card(
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Visitor Information',
                    style: theme.textTheme.headlineSmall?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 16),

                  _buildInfoRow(
                    context,
                    'Name',
                    visitorDetails.visitorName,
                    Icons.person,
                  ),
                  const SizedBox(height: 12),

                  _buildInfoRow(
                    context,
                    'Permission Level',
                    visitorDetails.permissionLevel.value,
                    _getPermissionIcon(visitorDetails.permissionLevel),
                    valueColor: _getPermissionColor(
                      visitorDetails.permissionLevel,
                    ),
                  ),
                  const SizedBox(height: 12),

                  _buildInfoRow(
                    context,
                    'Face ID',
                    '${visitorDetails.faceTagId.substring(0, 12)}...',
                    Icons.fingerprint,
                  ),
                  const SizedBox(height: 12),

                  _buildInfoRow(
                    context,
                    'Created',
                    dateFormat.format(visitorDetails.createdAt),
                    Icons.access_time,
                  ),

                  if (visitorDetails.lastUpdatedAt !=
                      visitorDetails.createdAt) ...[
                    const SizedBox(height: 12),
                    _buildInfoRow(
                      context,
                      'Last Updated',
                      dateFormat.format(visitorDetails.lastUpdatedAt),
                      Icons.update,
                    ),
                  ],
                ],
              ),
            ),
          ),
          const SizedBox(height: 24),

          // Botões de ação
          Row(
            children: [
              Expanded(
                child: OutlinedButton.icon(
                  onPressed:
                      () => _showEditDialog(
                        context,
                        visitorDetails.toVisitorPermission(),
                      ),
                  icon: const Icon(Icons.edit),
                  label: const Text('Edit Permission'),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: ElevatedButton.icon(
                  onPressed:
                      () => _showDeleteConfirmation(
                        context,
                        visitorDetails.toVisitorPermission(),
                      ),
                  icon: const Icon(Icons.delete),
                  label: const Text('Delete'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.red,
                    foregroundColor: Colors.white,
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildInfoRow(
    BuildContext context,
    String label,
    String value,
    IconData icon, {
    Color? valueColor,
  }) {
    final theme = Theme.of(context);

    return Row(
      children: [
        Icon(icon, size: 20, color: Colors.grey[600]),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                label,
                style: theme.textTheme.bodySmall?.copyWith(
                  color: Colors.grey[600],
                  fontWeight: FontWeight.w500,
                ),
              ),
              const SizedBox(height: 2),
              Text(
                value,
                style: theme.textTheme.bodyMedium?.copyWith(
                  color: valueColor,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  Color _getPermissionColor(PermissionLevel level) {
    switch (level) {
      case PermissionLevel.allowed:
        return Colors.green;
      case PermissionLevel.denied:
        return Colors.red;
    }
  }

  IconData _getPermissionIcon(PermissionLevel level) {
    switch (level) {
      case PermissionLevel.allowed:
        return Icons.check_circle;
      case PermissionLevel.denied:
        return Icons.block;
    }
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
        Navigator.of(context).pop(); // Voltar para a tela anterior após deletar
      },
    );
  }
}
