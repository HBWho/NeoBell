import 'package:flutter/material.dart';
import '../../../../core/common/widgets/base_screen_widget.dart';

class AllActivitiesScreen extends StatelessWidget {
  const AllActivitiesScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return BaseScreenWidget(
      title: 'Todas as Atividades',
      body: const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.list_alt,
              size: 80,
              color: Colors.grey,
            ),
            SizedBox(height: 20),
            Text(
              'Ver Todas as Atividades',
              style: TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.bold,
                color: Colors.grey,
              ),
            ),
            SizedBox(height: 10),
            Text(
              'Aqui você verá todas as atividades\nincluindo vídeos e entregas',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 16,
                color: Colors.grey,
              ),
            ),
          ],
        ),
      ),
    );
  }
} 