import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/utils/show_snackbar.dart';
import '../../domain/entities/package_delivery.dart';
import '../../domain/entities/package_delivery_filter.dart';
import '../../domain/entities/update_package_delivery.dart';
import '../blocs/package_delivery_bloc.dart';
import '../blocs/package_delivery_event.dart';
import '../blocs/package_delivery_state.dart';
import '../widgets/add_package_delivery_dialog.dart';
import '../widgets/package_delivery_item.dart';
import '../widgets/package_delivery_filter_dialog.dart';

class PackageDeliveriesScreen extends StatefulWidget {
  const PackageDeliveriesScreen({super.key});

  @override
  State<PackageDeliveriesScreen> createState() =>
      _PackageDeliveriesScreenState();
}

class _PackageDeliveriesScreenState extends State<PackageDeliveriesScreen> {
  final ScrollController _scrollController = ScrollController();
  PackageDeliveryFilter? _currentFilter;

  @override
  void initState() {
    super.initState();
    _scrollController.addListener(_onScroll);
    _initializePackageDeliveries();
  }

  void _initializePackageDeliveries() {
    final currentState = context.read<PackageDeliveryBloc>().state;
    if (currentState is PackageDeliveryInitial) {
      context.read<PackageDeliveryBloc>().add(const LoadPackageDeliveries());
    }
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  void _onScroll() {
    if (_isBottom) {
      context.read<PackageDeliveryBloc>().add(
        const LoadMorePackageDeliveries(),
      );
    }
  }

  bool get _isBottom {
    if (!_scrollController.hasClients) return false;
    final maxScroll = _scrollController.position.maxScrollExtent;
    final currentScroll = _scrollController.offset;
    return currentScroll >= (maxScroll * 0.9);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Package Deliveries'),
        actions: [
          IconButton(
            icon: const Icon(Icons.filter_list),
            onPressed: _showFilterDialog,
          ),
          IconButton(
            icon: const Icon(Icons.add),
            onPressed: _showAddDeliveryDialog,
          ),
        ],
      ),
      body: BlocConsumer<PackageDeliveryBloc, PackageDeliveryState>(
        listener: (context, state) {
          if (state is PackageDeliveryError) {
            showSnackBar(context, message: state.message, isError: true);
          } else if (state is PackageDeliveryOperationSuccess) {
            showSnackBar(context, message: state.message, isSucess: true);
          }
        },
        builder: (context, state) {
          if (state is PackageDeliveryLoading) {
            return const Center(child: CircularProgressIndicator());
          }

          if (state is PackageDeliveryError && state.deliveries.isEmpty) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.error_outline, size: 64, color: Colors.grey[400]),
                  const SizedBox(height: 16),
                  Text(
                    'Error loading deliveries',
                    style: Theme.of(context).textTheme.headlineSmall,
                  ),
                  const SizedBox(height: 8),
                  Text(
                    state.message,
                    textAlign: TextAlign.center,
                    style: Theme.of(context).textTheme.bodyMedium,
                  ),
                  const SizedBox(height: 16),
                  ElevatedButton(
                    onPressed: () {
                      context.read<PackageDeliveryBloc>().add(
                        const RefreshPackageDeliveries(),
                      );
                    },
                    child: const Text('Retry'),
                  ),
                ],
              ),
            );
          }
          final hasFilter = _currentFilter?.hasActiveFilters ?? false;

          if (state.deliveries.isEmpty) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(
                    Icons.local_shipping_outlined,
                    size: 64,
                    color: Colors.grey[400],
                  ),
                  const SizedBox(height: 16),
                  Text(
                    hasFilter ? 'No deliveries found' : 'No deliveries yet',
                    style: Theme.of(context).textTheme.headlineSmall,
                  ),
                  const SizedBox(height: 8),
                  Text(
                    hasFilter
                        ? 'Try adjusting your filters'
                        : 'Add your first package delivery',
                    style: Theme.of(context).textTheme.bodyMedium,
                  ),
                  const SizedBox(height: 16),
                  if (!hasFilter)
                    ElevatedButton.icon(
                      onPressed: _showAddDeliveryDialog,
                      icon: const Icon(Icons.add),
                      label: const Text('Add Delivery'),
                    ),
                ],
              ),
            );
          }

          return RefreshIndicator(
            onRefresh: () async {
              context.read<PackageDeliveryBloc>().add(
                const RefreshPackageDeliveries(),
              );
            },
            child: Column(
              children: [
                if (hasFilter) _buildFilterChips(),
                Expanded(
                  child: ListView.builder(
                    controller: _scrollController,
                    itemCount:
                        state.deliveries.length +
                        (state is PackageDeliveryLoadingMore ? 1 : 0),
                    itemBuilder: (context, index) {
                      if (index >= state.deliveries.length) {
                        return const Center(
                          child: Padding(
                            padding: EdgeInsets.all(16.0),
                            child: CircularProgressIndicator(),
                          ),
                        );
                      }

                      final delivery = state.deliveries[index];
                      return PackageDeliveryItem(
                        delivery: delivery,
                        onTap:
                            () => context.goNamed(
                              'package-delivery-details',
                              pathParameters: {'orderId': delivery.orderId},
                            ),
                        onEdit: () => _editDelivery(delivery),
                        onDelete: () => _deleteDelivery(delivery),
                        onMarkAsRetrieved: () => _markAsRetrieved(delivery),
                      );
                    },
                  ),
                ),
              ],
            ),
          );
        },
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _showAddDeliveryDialog,
        child: const Icon(Icons.add),
      ),
    );
  }

  Widget _buildFilterChips() {
    return Container(
      padding: const EdgeInsets.all(16),
      child: Row(
        children: [
          Expanded(
            child: Wrap(
              spacing: 8,
              children: [
                if (_currentFilter?.status != null)
                  Chip(
                    label: Text(_currentFilter!.status!.displayName),
                    onDeleted: () => _removeStatusFilter(),
                  ),
                if (_currentFilter?.searchTerm != null)
                  Chip(
                    label: Text('Search: ${_currentFilter!.searchTerm}'),
                    onDeleted: () => _removeSearchFilter(),
                  ),
                if (_currentFilter?.startDate != null ||
                    _currentFilter?.endDate != null)
                  Chip(
                    label: const Text('Date Filter'),
                    onDeleted: () => _removeDateFilter(),
                  ),
              ],
            ),
          ),
          TextButton(
            onPressed: _clearAllFilters,
            child: const Text('Clear All'),
          ),
        ],
      ),
    );
  }

  void _showFilterDialog() async {
    final filter = await showDialog<PackageDeliveryFilter>(
      context: context,
      builder:
          (context) =>
              PackageDeliveryFilterDialog(currentFilter: _currentFilter),
    );

    if (filter != null) {
      setState(() {
        _currentFilter = filter;
      });
      context.read<PackageDeliveryBloc>().add(ApplyFilterEvent(filter));
    }
  }

  void _showAddDeliveryDialog() {
    showDialog(
      context: context,
      builder: (context) => const AddPackageDeliveryDialog(),
    );
  }

  void _editDelivery(PackageDelivery delivery) {
    showDialog(
      context: context,
      builder: (context) => AddPackageDeliveryDialog(delivery: delivery),
    );
  }

  void _deleteDelivery(PackageDelivery delivery) {
    showDialog(
      context: context,
      builder:
          (context) => AlertDialog(
            title: const Text('Delete Delivery'),
            content: Text(
              'Are you sure you want to delete "${delivery.itemDescription}"?',
            ),
            actions: [
              TextButton(
                onPressed: () => context.pop(),
                child: const Text('Cancel'),
              ),
              ElevatedButton(
                onPressed: () {
                  context.pop();
                  context.read<PackageDeliveryBloc>().add(
                    DeletePackageDeliveryEvent(delivery.orderId),
                  );
                },
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.red,
                  foregroundColor: Colors.white,
                ),
                child: const Text('Delete'),
              ),
            ],
          ),
    );
  }

  void _markAsRetrieved(PackageDelivery delivery) {
    if (delivery.isRetrieved) return;

    showDialog(
      context: context,
      builder:
          (context) => AlertDialog(
            title: const Text('Mark as Retrieved'),
            content: Text('Mark "${delivery.itemDescription}" as retrieved?'),
            actions: [
              TextButton(
                onPressed: () => context.pop(),
                child: const Text('Cancel'),
              ),
              ElevatedButton(
                onPressed: () {
                  context.pop();
                  context.read<PackageDeliveryBloc>().add(
                    UpdatePackageDeliveryEvent(
                      orderId: delivery.orderId,
                      delivery: const UpdatePackageDelivery(
                        status: PackageDeliveryStatus.retrievedByUser,
                      ),
                    ),
                  );
                },
                child: const Text('Mark Retrieved'),
              ),
            ],
          ),
    );
  }

  void _removeStatusFilter() {
    if (_currentFilter != null) {
      final newFilter = _currentFilter!.copyWith(status: null);
      setState(() {
        _currentFilter = newFilter.hasActiveFilters ? newFilter : null;
      });
      context.read<PackageDeliveryBloc>().add(
        newFilter.hasActiveFilters
            ? ApplyFilterEvent(newFilter)
            : const ClearFilterEvent(),
      );
    }
  }

  void _removeSearchFilter() {
    if (_currentFilter != null) {
      final newFilter = _currentFilter!.copyWith(searchTerm: '');
      setState(() {
        _currentFilter = newFilter.hasActiveFilters ? newFilter : null;
      });
      context.read<PackageDeliveryBloc>().add(
        newFilter.hasActiveFilters
            ? ApplyFilterEvent(newFilter)
            : const ClearFilterEvent(),
      );
    }
  }

  void _removeDateFilter() {
    if (_currentFilter != null) {
      final newFilter = _currentFilter!.copyWith(
        startDate: null,
        endDate: null,
      );
      setState(() {
        _currentFilter = newFilter.hasActiveFilters ? newFilter : null;
      });
      context.read<PackageDeliveryBloc>().add(
        newFilter.hasActiveFilters
            ? ApplyFilterEvent(newFilter)
            : const ClearFilterEvent(),
      );
    }
  }

  void _clearAllFilters() {
    setState(() {
      _currentFilter = null;
    });
    context.read<PackageDeliveryBloc>().add(const ClearFilterEvent());
  }
}
