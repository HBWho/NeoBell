import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../../../core/common/widgets/base_screen_widget.dart';
import '../../../../core/utils/show_snackbar.dart';
import '../../domain/entities/activity_log.dart';
import '../../domain/entities/activity_log_filter.dart';
import '../blocs/activity_log_bloc.dart';
import '../widgets/activity_log_item.dart';
import '../widgets/activity_log_filter_dialog.dart';
import 'activity_log_details_screen.dart';

class ActivityLogsScreen extends StatefulWidget {
  const ActivityLogsScreen({super.key});

  @override
  State<ActivityLogsScreen> createState() => _ActivityLogsScreenState();
}

class _ActivityLogsScreenState extends State<ActivityLogsScreen> {
  final ScrollController _scrollController = ScrollController();
  ActivityLogFilter _currentFilter = const ActivityLogFilter(limit: 20);

  @override
  void initState() {
    super.initState();
    //_scrollController.addListener(_onScroll);
    final currentState = context.read<ActivityLogBloc>().state;
    if (currentState is ActivityLogInitial) {
      context.read<ActivityLogBloc>().add(
        LoadActivityLogs(filter: _currentFilter),
      );
    }
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  void _onScroll() {
    if (_scrollController.position.pixels >=
        _scrollController.position.maxScrollExtent * 0.9) {
      final state = context.read<ActivityLogBloc>().state;
      if (state is ActivityLogLoaded && state.hasMore) {
        context.read<ActivityLogBloc>().add(LoadMoreActivityLogs());
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return BaseScreenWidget(
      title: 'Activity Logs',
      actions: [
        IconButton(
          icon: const Icon(Icons.filter_list),
          onPressed: () => _showFilterDialog(),
        ),
        IconButton(
          icon: const Icon(Icons.refresh),
          onPressed: () {
            context.read<ActivityLogBloc>().add(RefreshActivityLogs());
          },
        ),
      ],
      body: BlocConsumer<ActivityLogBloc, ActivityLogState>(
        listener: (context, state) {
          if (state is ActivityLogFailure) {
            showSnackBar(context, message: state.message, isError: true);
          }
        },
        builder: (context, state) {
          if (state is ActivityLogLoading && state.activityLogs.isEmpty) {
            return const Center(child: CircularProgressIndicator());
          } else if (state is ActivityLogFailure &&
              state.activityLogs.isEmpty) {
            return _buildErrorWidget(state.message);
          }

          if (state.activityLogs.isEmpty) {
            return _buildEmptyWidget();
          }

          return RefreshIndicator(
            onRefresh: () async {
              context.read<ActivityLogBloc>().add(RefreshActivityLogs());
            },
            child: ListView.builder(
              controller: _scrollController,
              padding: const EdgeInsets.all(16),
              itemCount:
                  state.activityLogs.length +
                  (state is ActivityLogLoadingMore ? 1 : 0),
              itemBuilder: (context, index) {
                if (index >= state.activityLogs.length) {
                  return const Center(
                    child: Padding(
                      padding: EdgeInsets.all(16),
                      child: CircularProgressIndicator(),
                    ),
                  );
                }

                final activityLog = state.activityLogs[index];
                return ActivityLogItem(
                  activityLog: activityLog,
                  onTap: () => _navigateToDetails(context, activityLog),
                );
              },
            ),
          );
        },
      ),
    );
  }

  Widget _buildErrorWidget(String message) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.error_outline, size: 64, color: Colors.red),
          const SizedBox(height: 16),
          Text(
            'Error loading activity logs',
            style: TextStyle(fontSize: 18, color: Colors.red[700]),
          ),
          const SizedBox(height: 8),
          Text(
            message,
            textAlign: TextAlign.center,
            style: const TextStyle(color: Colors.grey),
          ),
          const SizedBox(height: 16),
          ElevatedButton(
            onPressed: () {
              context.read<ActivityLogBloc>().add(
                LoadActivityLogs(filter: _currentFilter),
              );
            },
            child: const Text('Retry'),
          ),
        ],
      ),
    );
  }

  Widget _buildEmptyWidget() {
    return const Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.history, size: 64, color: Colors.grey),
          SizedBox(height: 16),
          Text(
            'No activity logs found',
            style: TextStyle(fontSize: 18, color: Colors.grey),
          ),
          SizedBox(height: 8),
          Text(
            'Activity logs will appear here when events occur on your devices',
            textAlign: TextAlign.center,
            style: TextStyle(color: Colors.grey),
          ),
        ],
      ),
    );
  }

  void _showFilterDialog() {
    showDialog(
      context: context,
      builder:
          (context) => ActivityLogFilterDialog(
            currentFilter: _currentFilter,
            onApplyFilter: (filter) {
              setState(() {
                _currentFilter = filter;
              });
              context.read<ActivityLogBloc>().add(
                ApplyActivityLogFilter(filter: filter),
              );
            },
          ),
    );
  }

  void _navigateToDetails(BuildContext context, ActivityLog activityLog) {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder:
            (context) => ActivityLogDetailsScreen(
              logSourceId: activityLog.logSourceId,
              timestampUuid: activityLog.timestampUuid,
            ),
      ),
    );
  }
}
