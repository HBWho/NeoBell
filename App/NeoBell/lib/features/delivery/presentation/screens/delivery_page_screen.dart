import 'package:flutter/material.dart';
import '../../../../core/common/widgets/base_screen_widget.dart';

class DeliveryPageScreen extends StatelessWidget {
  const DeliveryPageScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return BaseScreenWidget(
      title: 'Página de Entregas',
      body: const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.local_shipping,
              size: 80,
              color: Colors.orange,
            ),
            SizedBox(height: 20),
            Text(
              'Página de Entregas',
              style: TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.bold,
                color: Colors.grey,
              ),
            ),
            SizedBox(height: 10),
            Text(
              'Aqui você verá todas as informações\nsobre suas entregas',
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