import 'package:flutter/material.dart';
import '../../../../core/common/widgets/base_screen_widget.dart';
import '../../../../core/utils/show_snackbar.dart';

class CreateDeliveryScreen extends StatefulWidget {
  const CreateDeliveryScreen({super.key});

  @override
  State<CreateDeliveryScreen> createState() => _CreateDeliveryScreenState();
}

class _CreateDeliveryScreenState extends State<CreateDeliveryScreen> {
  final _formKey = GlobalKey<FormState>();
  final _packageNumberController = TextEditingController();
  final _packageNameController = TextEditingController();
  final _companyController = TextEditingController();

  bool _isLoading = false;

  @override
  void dispose() {
    _packageNumberController.dispose();
    _packageNameController.dispose();
    _companyController.dispose();
    super.dispose();
  }

  Future<void> _submitDelivery() async {
    if (_formKey.currentState?.validate() ?? false) {
      setState(() {
        _isLoading = true;
      });

      // Simulate API call delay
      await Future.delayed(const Duration(seconds: 1));

      if (mounted) {
        setState(() {
          _isLoading = false;
        });

        // Show success message
        showSnackBar(
          context,
          message: 'Entrega registrada com sucesso!',
          isError: false,
        );

        // Clear the form
        _packageNumberController.clear();
        _packageNameController.clear();
        _companyController.clear();
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return BaseScreenWidget(
      title: 'Criar Entrega',
      body: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          children: [
            // Header Section
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: Colors.blue.shade50,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: Colors.blue.shade200),
              ),
              child: Column(
                children: [
                  Icon(
                    Icons.add_box,
                    size: 48,
                    color: Colors.blue.shade600,
                  ),
                  const SizedBox(height: 12),
                  Text(
                    'Registrar Nova Entrega',
                    style: TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                      color: Colors.blue.shade800,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Preencha as informações abaixo para registrar uma entrega esperada',
                    textAlign: TextAlign.center,
                    style: TextStyle(
                      fontSize: 14,
                      color: Colors.blue.shade600,
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
                    // Package Number Field
                    TextFormField(
                      controller: _packageNumberController,
                      validator: (value) {
                        if (value == null || value.trim().isEmpty) {
                          return 'Número do pacote é obrigatório';
                        }
                        if (value.trim().length < 3) {
                          return 'Número do pacote deve ter pelo menos 3 caracteres';
                        }
                        return null;
                      },
                      decoration: InputDecoration(
                        labelText: 'Número do Pacote',
                        hintText: 'Ex: BR123456789',
                        prefixIcon: const Icon(Icons.qr_code),
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                        focusedBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12),
                          borderSide: const BorderSide(color: Colors.blue, width: 2),
                        ),
                      ),
                      textCapitalization: TextCapitalization.characters,
                    ),
                    const SizedBox(height: 20),

                    // Package Name Field
                    TextFormField(
                      controller: _packageNameController,
                      validator: (value) {
                        if (value == null || value.trim().isEmpty) {
                          return 'Nome do pacote é obrigatório';
                        }
                        if (value.trim().length < 2) {
                          return 'Nome do pacote deve ter pelo menos 2 caracteres';
                        }
                        return null;
                      },
                      decoration: InputDecoration(
                        labelText: 'Nome do Pacote',
                        hintText: 'Ex: Samsung Galaxy S24, Kindle, Livros',
                        prefixIcon: const Icon(Icons.inventory_2),
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                        focusedBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12),
                          borderSide: const BorderSide(color: Colors.blue, width: 2),
                        ),
                      ),
                      textCapitalization: TextCapitalization.words,
                    ),
                    const SizedBox(height: 20),

                    // Company Field
                    TextFormField(
                      controller: _companyController,
                      validator: (value) {
                        if (value == null || value.trim().isEmpty) {
                          return 'Empresa é obrigatória';
                        }
                        if (value.trim().length < 2) {
                          return 'Nome da empresa deve ter pelo menos 2 caracteres';
                        }
                        return null;
                      },
                      decoration: InputDecoration(
                        labelText: 'Empresa',
                        hintText: 'Ex: Amazon, Mercado Livre, Shopee',
                        prefixIcon: const Icon(Icons.business),
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12),
                        ),
                        focusedBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12),
                          borderSide: const BorderSide(color: Colors.blue, width: 2),
                        ),
                      ),
                      textCapitalization: TextCapitalization.words,
                    ),
                    
                    const Spacer(),

                    // Submit Button (positioned at bottom right)
                    Row(
                      mainAxisAlignment: MainAxisAlignment.end,
                      children: [
                        ElevatedButton.icon(
                          onPressed: _isLoading ? null : _submitDelivery,
                          icon: _isLoading
                              ? const SizedBox(
                                  width: 16,
                                  height: 16,
                                  child: CircularProgressIndicator(
                                    strokeWidth: 2,
                                    valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                                  ),
                                )
                              : const Icon(Icons.send),
                          label: Text(_isLoading ? 'Registrando...' : 'Registrar Entrega'),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: Colors.green,
                            foregroundColor: Colors.white,
                            padding: const EdgeInsets.symmetric(
                              horizontal: 24,
                              vertical: 14,
                            ),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(12),
                            ),
                            elevation: 3,
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