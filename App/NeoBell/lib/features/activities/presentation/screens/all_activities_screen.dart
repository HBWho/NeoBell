import 'package:flutter/material.dart';
import '../../../../core/common/widgets/base_screen_widget.dart';
import '../../../../core/services/all_activities_screen.dart';

class AllActivitiesScreen extends StatefulWidget {
  const AllActivitiesScreen({super.key});

  @override
  State<AllActivitiesScreen> createState() => _AllActivitiesScreenState();
}

class _AllActivitiesScreenState extends State<AllActivitiesScreen> {
  late Future<List<Map<String, String>>> _futureNotifications;

  @override
  void initState() {
    super.initState();
    _futureNotifications = NotificationService().getAllNotifications();
  }

  @override
  Widget build(BuildContext context) {
    return BaseScreenWidget(
      title: 'All Activities',
      body: FutureBuilder<List<Map<String, String>>>(
        future: _futureNotifications,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          if (snapshot.hasError) {
            return const Center(child: Text('Error loading notifications'));
          }

          final notifications = snapshot.data ?? [];

          return ListView.builder(
            padding: const EdgeInsets.symmetric(vertical: 16),
            itemCount: notifications.length,
            itemBuilder: (context, index) {
              final notification = notifications[index];
              return Container(
                margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.lightBlue.shade100,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Row(
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            notification['name'] ?? '',
                            style: const TextStyle(fontWeight: FontWeight.bold),
                          ),
                          const SizedBox(height: 4),
                          Text(notification['message'] ?? ''),
                        ],
                      ),
                    ),
                    if ((notification['date'] ?? '').isNotEmpty)
                      Padding(
                        padding: const EdgeInsets.only(left: 8.0),
                        child: Text(
                          notification['date']!,
                          style: const TextStyle(fontWeight: FontWeight.bold),
                        ),
                      ),
                  ],
                ),
              );
            },
          );
        },
      ),
      bottomNavigationBar: Padding(
        padding: const EdgeInsets.all(12.0),
        child: ElevatedButton(
          style: ElevatedButton.styleFrom(
            backgroundColor: Colors.black,
            foregroundColor: Colors.white,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(8),
              side: const BorderSide(color: Colors.red),
            ),
          ),
          onPressed: () => Navigator.pop(context),
          child: const Text('Return'),
        ),
      ),
    );
  }
}
