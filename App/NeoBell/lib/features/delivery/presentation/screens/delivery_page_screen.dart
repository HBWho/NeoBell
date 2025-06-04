import 'package:flutter/material.dart';
import '../../../../core/common/widgets/base_screen_widget.dart';
import '../../../../core/services/delivery_service.dart';
import 'package:go_router/go_router.dart';

class DeliveryPageScreen extends StatefulWidget {
  const DeliveryPageScreen({super.key});

  @override
  State<DeliveryPageScreen> createState() => _DeliveryPageScreenState();
}

class _DeliveryPageScreenState extends State<DeliveryPageScreen> {
  late Future<List<Map<String, String>>> _futureDeliveries;

  @override
  void initState() {
    super.initState();
    _futureDeliveries = DeliveryService().getDeliveryActivities();
  }

  @override
  Widget build(BuildContext context) {
    return BaseScreenWidget(
      title: 'Delivery Page',
      body: FutureBuilder<List<Map<String, String>>>(
        future: _futureDeliveries,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }

          if (snapshot.hasError) {
            return const Center(child: Text('Error loading delivery data'));
          }

          final activities = snapshot.data ?? [];

          return ListView.builder(
            padding: const EdgeInsets.symmetric(vertical: 16),
            itemCount: activities.length,
            itemBuilder: (context, index) {
              final activity = activities[index];
              return Container(
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
                      activity['name'] ?? '',
                      style: const TextStyle(fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 4),
                    Text(activity['message'] ?? ''),
                  ],
                ),
              );
            },
          );
        },
      ),
      bottomNavigationBar: Padding(
        padding: const EdgeInsets.all(12.0),
        child: Row(
          children: [
            Expanded(
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
            const SizedBox(width: 10),
            Expanded(
              child: ElevatedButton(
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.teal,
                  foregroundColor: Colors.white,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(8),
                  ),
                ),
                onPressed: () {
                  context.goNamed('delivery-records');
                },
                child: const Text('All Delivery Records'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
