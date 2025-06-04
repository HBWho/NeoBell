import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/common/widgets/base_screen_widget.dart';
import '../../../../core/services/visitor_notification_service.dart';

class VisitorNotificationsScreen extends StatefulWidget {
  const VisitorNotificationsScreen({super.key});

  @override
  State<VisitorNotificationsScreen> createState() => _VisitorNotificationsScreenState();
}

class _VisitorNotificationsScreenState extends State<VisitorNotificationsScreen> {
  late Future<List<Map<String, String>>> _futureNotifications;

  @override
  void initState() {
    super.initState();
    _futureNotifications = VisitorNotificationService().getVisitorVideos();
  }

  @override
  Widget build(BuildContext context) {
    return BaseScreenWidget(
      title: 'Notification Visitor Page',
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
              return GestureDetector(
                onTap: () {
                  context.pushNamed(
                    'visitor-notification-detail',
                    extra: notification,
                  );
                },
                child: Container(
                  margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: Colors.lightBlue.shade100,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        notification['name'] ?? '',
                        style: const TextStyle(fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 4),
                      const Text('left a video message'),
                    ],
                  ),
                ),
              );
            },
          );
        },
      ),
      bottomNavigationBar: Padding(
        padding: const EdgeInsets.all(12.0),
        child: ElevatedButton(
          onPressed: () => Navigator.pop(context),
          style: ElevatedButton.styleFrom(
            backgroundColor: Colors.black,
            foregroundColor: Colors.white,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(8),
              side: const BorderSide(color: Colors.red),
            ),
          ),
          child: const Text('Return'),
        ),
      ),
    );
  }
}
