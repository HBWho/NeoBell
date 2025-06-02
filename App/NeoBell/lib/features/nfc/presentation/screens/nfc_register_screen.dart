import 'package:flutter/material.dart';
import '../../../../core/common/widgets/base_screen_widget.dart';

class NfcRegisterScreen extends StatelessWidget {
  const NfcRegisterScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return BaseScreenWidget(
      title: 'Registro NFC',
      body: const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.nfc,
              size: 80,
              color: Colors.deepOrange,
            ),
            SizedBox(height: 20),
            Text(
              'Registro NFC',
              style: TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.bold,
                color: Colors.grey,
              ),
            ),
            SizedBox(height: 10),
            Text(
              'Registre sua tag RFID para\nretirar pacotes de entrega',
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