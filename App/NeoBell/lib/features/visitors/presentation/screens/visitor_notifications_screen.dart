import 'package:flutter/material.dart';
import '../../../../core/common/widgets/base_screen_widget.dart';

class VisitorNotificationsScreen extends StatelessWidget {
  const VisitorNotificationsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return BaseScreenWidget(
      title: 'Notificações de Visitantes',
      body: const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.video_call,
              size: 80,
              color: Colors.blue,
            ),
            SizedBox(height: 20),
            Text(
              'Notificações de Visitantes',
              style: TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.bold,
                color: Colors.grey,
              ),
            ),
            SizedBox(height: 10),
            Text(
              'Aqui você verá todos os vídeos\ne interações com visitantes',
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