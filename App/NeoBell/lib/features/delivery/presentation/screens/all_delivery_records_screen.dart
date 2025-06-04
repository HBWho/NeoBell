import 'package:flutter/material.dart';
import '../../../../core/common/widgets/base_screen_widget.dart';
import '../../../../core/services/delivery_records_service.dart';

class AllDeliveryRecordsScreen extends StatefulWidget {
  const AllDeliveryRecordsScreen({super.key});

  @override
  State<AllDeliveryRecordsScreen> createState() => _AllDeliveryRecordsScreenState();
}

class _AllDeliveryRecordsScreenState extends State<AllDeliveryRecordsScreen> {
  late Future<List<Map<String, String>>> _futureRecords;

  @override
  void initState() {
    super.initState();
    _futureRecords = DeliveryRecordsService().getAllDeliveryRecords();
  }

  @override
  Widget build(BuildContext context) {
    return BaseScreenWidget(
      title: 'All Delivery Register',
      body: FutureBuilder<List<Map<String, String>>>(
        future: _futureRecords,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }

          if (snapshot.hasError) {
            return const Center(child: Text('Error loading delivery records'));
          }

          final records = snapshot.data ?? [];

          return ListView.builder(
            padding: const EdgeInsets.symmetric(vertical: 16),
            itemCount: records.length,
            itemBuilder: (context, index) {
              final record = records[index];
              return Container(
                margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.pink.shade100,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '${record['code']}, ${record['type']}',
                      style: const TextStyle(fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 4),
                    Text(record['description'] ?? ''),
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
