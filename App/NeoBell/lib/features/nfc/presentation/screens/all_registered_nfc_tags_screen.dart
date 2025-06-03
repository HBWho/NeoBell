import 'package:flutter/material.dart';
import '../../../../core/common/widgets/base_screen_widget.dart';

class AllRegisteredNfcTagsScreen extends StatefulWidget {
  const AllRegisteredNfcTagsScreen({super.key});

  @override
  State<AllRegisteredNfcTagsScreen> createState() => _AllRegisteredNfcTagsScreenState();
}

class _AllRegisteredNfcTagsScreenState extends State<AllRegisteredNfcTagsScreen> {
  // Mock data for registered NFC tags
  List<Map<String, dynamic>> _registeredTags = [
    {
      'id': '04-AF-98-C2',
      'userName': 'João Silva',
      'isAllowed': true,
      'registeredDate': '15/01/2024',
    },
    {
      'id': '12-BC-45-D7',
      'userName': 'Maria Santos',
      'isAllowed': true,
      'registeredDate': '12/01/2024',
    },
    {
      'id': '7A-E3-22-FF',
      'userName': 'Pedro Costa',
      'isAllowed': false,
      'registeredDate': '10/01/2024',
    },
    {
      'id': '89-44-AB-11',
      'userName': 'Ana Oliveira',
      'isAllowed': true,
      'registeredDate': '08/01/2024',
    },
  ];

  void _toggleTagStatus(int index) {
    setState(() {
      _registeredTags[index]['isAllowed'] = !_registeredTags[index]['isAllowed'];
    });
    
    // Show feedback to user
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          _registeredTags[index]['isAllowed'] 
            ? 'Tag de ${_registeredTags[index]['userName']} ativada'
            : 'Tag de ${_registeredTags[index]['userName']} desativada',
        ),
        backgroundColor: _registeredTags[index]['isAllowed'] 
          ? Colors.green 
          : Colors.orange,
        duration: const Duration(seconds: 2),
      ),
    );
  }

  void _deleteTag(int index) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Remover Tag'),
        content: Text(
          'Deseja remover a tag de ${_registeredTags[index]['userName']}?',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancelar'),
          ),
          ElevatedButton(
            onPressed: () {
              setState(() {
                _registeredTags.removeAt(index);
              });
              Navigator.pop(context);
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                  content: Text('Tag removida com sucesso'),
                  backgroundColor: Colors.red,
                ),
              );
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.red,
              foregroundColor: Colors.white,
            ),
            child: const Text('Remover'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return BaseScreenWidget(
      title: 'Tags NFC Registradas',
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            // Header with count
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.blue.shade50,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: Colors.blue.shade200),
              ),
              child: Row(
                children: [
                  Icon(
                    Icons.nfc,
                    color: Colors.blue.shade600,
                    size: 32,
                  ),
                  const SizedBox(width: 12),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Tags Registradas',
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                          color: Colors.blue.shade800,
                        ),
                      ),
                      Text(
                        '${_registeredTags.length} tag(s) registrada(s)',
                        style: TextStyle(
                          fontSize: 14,
                          color: Colors.blue.shade600,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),

            // Tags List
            Expanded(
              child: _registeredTags.isEmpty
                  ? Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(
                            Icons.nfc_outlined,
                            size: 64,
                            color: Colors.grey.shade400,
                          ),
                          const SizedBox(height: 16),
                          Text(
                            'Nenhuma tag registrada',
                            style: TextStyle(
                              fontSize: 18,
                              color: Colors.grey.shade600,
                            ),
                          ),
                        ],
                      ),
                    )
                  : ListView.builder(
                      itemCount: _registeredTags.length,
                      itemBuilder: (context, index) {
                        final tag = _registeredTags[index];
                        return Card(
                          margin: const EdgeInsets.only(bottom: 12),
                          elevation: 2,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: Padding(
                            padding: const EdgeInsets.all(16),
                            child: Row(
                              children: [
                                // User Avatar
                                CircleAvatar(
                                  backgroundColor: tag['isAllowed'] 
                                    ? Colors.green.shade100 
                                    : Colors.grey.shade200,
                                  child: Icon(
                                    Icons.person,
                                    color: tag['isAllowed'] 
                                      ? Colors.green.shade600 
                                      : Colors.grey.shade600,
                                  ),
                                ),
                                const SizedBox(width: 16),
                                
                                // Tag Info
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        tag['userName'],
                                        style: const TextStyle(
                                          fontSize: 16,
                                          fontWeight: FontWeight.bold,
                                        ),
                                      ),
                                      const SizedBox(height: 4),
                                      Text(
                                        'ID: ${tag['id']}',
                                        style: TextStyle(
                                          fontSize: 12,
                                          color: Colors.grey.shade600,
                                          fontFamily: 'monospace',
                                        ),
                                      ),
                                      const SizedBox(height: 4),
                                      Text(
                                        'Registrado em: ${tag['registeredDate']}',
                                        style: TextStyle(
                                          fontSize: 12,
                                          color: Colors.grey.shade500,
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                                
                                // Allow Toggle Switch
                                Column(
                                  children: [
                                    Text(
                                      'Permitir',
                                      style: TextStyle(
                                        fontSize: 12,
                                        color: Colors.grey.shade600,
                                      ),
                                    ),
                                    Switch(
                                      value: tag['isAllowed'],
                                      onChanged: (value) => _toggleTagStatus(index),
                                      activeColor: Colors.green,
                                    ),
                                  ],
                                ),
                                
                                // Delete Button
                                IconButton(
                                  onPressed: () => _deleteTag(index),
                                  icon: const Icon(
                                    Icons.delete,
                                    color: Colors.red,
                                  ),
                                  tooltip: 'Remover tag',
                                ),
                              ],
                            ),
                          ),
                        );
                      },
                    ),
            ),
          ],
        ),
      ),
    );
  }
} 