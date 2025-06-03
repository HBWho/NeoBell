import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/common/widgets/base_screen_widget.dart';
import '../../../../core/utils/show_snackbar.dart';
import '../widgets/nfc_scan_dialog.dart';

class NfcRegisterScreen extends StatefulWidget {
  const NfcRegisterScreen({super.key});

  @override
  State<NfcRegisterScreen> createState() => _NfcRegisterScreenState();
}

class _NfcRegisterScreenState extends State<NfcRegisterScreen> {
  final _formKey = GlobalKey<FormState>();
  final _userNameController = TextEditingController();
  String? _scannedTagId;
  bool _isTagScanned = false;

  @override
  void dispose() {
    _userNameController.dispose();
    super.dispose();
  }

  Future<void> _scanNfcTag() async {
    if (_formKey.currentState?.validate() ?? false) {
      final result = await showDialog<String>(
        context: context,
        barrierDismissible: false,
        builder: (context) => const NfcScanDialog(),
      );

      if (result != null && mounted) {
        setState(() {
          _scannedTagId = result;
          _isTagScanned = true;
        });
      }
    } else {
      showSnackBar(
        context,
        message: 'Por favor, insira o nome do usuário primeiro',
        isError: true,
      );
    }
  }

  Future<void> _registerTag() async {
    if (_scannedTagId != null && _userNameController.text.isNotEmpty) {
      // Simulate API call
      await Future.delayed(const Duration(milliseconds: 800));
      
      if (mounted) {
        showSnackBar(
          context,
          message: 'Tag NFC registrada com sucesso para ${_userNameController.text}!',
          isError: false,
        );
        
        // Clear form
        _userNameController.clear();
        setState(() {
          _scannedTagId = null;
          _isTagScanned = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return BaseScreenWidget(
      title: 'Registro NFC',
      body: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          children: [
            // Header Section
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: Colors.deepOrange.shade50,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: Colors.deepOrange.shade200),
              ),
              child: Column(
                children: [
                  Icon(
                    Icons.nfc,
                    size: 48,
                    color: Colors.deepOrange.shade600,
                  ),
                  const SizedBox(height: 12),
                  Text(
                    'Registrar Tag NFC',
                    style: TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                      color: Colors.deepOrange.shade800,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Registre uma tag NFC para permitir retirada de pacotes',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      fontSize: 14,
                      color: Colors.deepOrange.shade600,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 30),

            // Form Section
            Expanded(
              child: Form(
                key: _formKey,
                child: Column(
                  children: [
                    // User Name Field
                    TextFormField(
                      controller: _userNameController,
                      validator: (value) {
                        if (value == null || value.trim().isEmpty) {
                          return 'Nome do usuário é obrigatório';
                        }
                        if (value.trim().length < 2) {
                          return 'Nome deve ter pelo menos 2 caracteres';
                        }
                        return null;
                      },
                      decoration: InputDecoration(
                        labelText: 'Nome do Usuário',
                        hintText: 'Ex: João Silva, Maria Santos',
                        prefixIcon: const Icon(Icons.person),
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                        focusedBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12),
                          borderSide: const BorderSide(color: Colors.deepOrange, width: 2),
                        ),
                      ),
                      textCapitalization: TextCapitalization.words,
                    ),
                    const SizedBox(height: 30),

                    // Scan NFC Button
                    SizedBox(
                      width: double.infinity,
                      height: 60,
                      child: ElevatedButton.icon(
                        onPressed: _scanNfcTag,
                        icon: const Icon(Icons.nfc, size: 28),
                        label: const Text(
                          'ESCANEAR NFC',
                          style: TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: Colors.deepOrange,
                          foregroundColor: Colors.white,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(12),
                          ),
                          elevation: 3,
                        ),
                      ),
                    ),
                    
                    const SizedBox(height: 20),

                    // Scanned Tag Info
                    if (_isTagScanned) ...[
                      Container(
                        width: double.infinity,
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          color: Colors.green.shade50,
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(color: Colors.green.shade200),
                        ),
                        child: Column(
                          children: [
                            Icon(
                              Icons.check_circle,
                              color: Colors.green.shade600,
                              size: 32,
                            ),
                            const SizedBox(height: 8),
                            Text(
                              'Tag NFC Detectada',
                              style: TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.bold,
                                color: Colors.green.shade800,
                              ),
                            ),
                            const SizedBox(height: 8),
                            Text(
                              'ID: $_scannedTagId',
                              style: TextStyle(
                                fontSize: 14,
                                color: Colors.green.shade700,
                                fontFamily: 'monospace',
                              ),
                            ),
                            const SizedBox(height: 16),
                            ElevatedButton.icon(
                              onPressed: _registerTag,
                              icon: const Icon(Icons.save),
                              label: const Text('Registrar Tag'),
                              style: ElevatedButton.styleFrom(
                                backgroundColor: Colors.green,
                                foregroundColor: Colors.white,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],

                    const Spacer(),

                    // All Registered Tags Button (bottom right)
                    Row(
                      mainAxisAlignment: MainAxisAlignment.end,
                      children: [
                        ElevatedButton.icon(
                          onPressed: () => context.push('/home/nfc-register/all-tags'),
                          icon: const Icon(Icons.list),
                          label: const Text('Todas Tags NFC'),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: Colors.blue,
                            foregroundColor: Colors.white,
                            padding: const EdgeInsets.symmetric(
                              horizontal: 20,
                              vertical: 12,
                            ),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(12),
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 20),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
} 