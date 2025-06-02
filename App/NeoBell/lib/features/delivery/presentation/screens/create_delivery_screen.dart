import 'package:flutter/material.dart';
import '../../../../core/common/widgets/base_screen_widget.dart';

class CreateDeliveryScreen extends StatelessWidget {
  const CreateDeliveryScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return BaseScreenWidget(
      title: 'Criar Entrega',
      body: const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.add_box,
              size: 80,
              color: Colors.green,
            ),
            SizedBox(height: 20),
            Text(
              'Criar Nova Entrega',
              style: TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.bold,
                color: Colors.grey,
              ),
            ),
            SizedBox(height: 10),
            Text(
              'Registre uma entrega para que\no módulo possa detectá-la',
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