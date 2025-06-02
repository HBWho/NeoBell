import 'package:flutter/material.dart';
import '../../../../core/common/widgets/base_screen_widget.dart';

class RegisteredMembersScreen extends StatelessWidget {
  const RegisteredMembersScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return BaseScreenWidget(
      title: 'Membros Registrados',
      body: const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.people,
              size: 80,
              color: Colors.purple,
            ),
            SizedBox(height: 20),
            Text(
              'Membros Registrados',
              style: TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.bold,
                color: Colors.grey,
              ),
            ),
            SizedBox(height: 10),
            Text(
              'Gerencie quais visitantes\npodem deixar mensagens',
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