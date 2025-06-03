import 'package:flutter/material.dart';
import '../../../../core/common/widgets/base_screen_widget.dart';
import '../widgets/add_visitor_dialog.dart';

class RegisteredMembersScreen extends StatefulWidget {
  const RegisteredMembersScreen({super.key});

  @override
  State<RegisteredMembersScreen> createState() => _RegisteredMembersScreenState();
}

class _RegisteredMembersScreenState extends State<RegisteredMembersScreen> {
  // Mock data for registered members
  List<Map<String, dynamic>> _registeredMembers = [
    {
      'id': '1',
      'name': 'João Silva',
      'surname': 'Silva',
      'email': 'joao.silva@email.com',
      'photo': 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&h=150&fit=crop&crop=face',
      'isAllowed': true,
      'registeredDate': '15/01/2024',
    },
    {
      'id': '2',
      'name': 'Maria Santos',
      'surname': 'Santos',
      'email': 'maria.santos@email.com',
      'photo': 'https://images.unsplash.com/photo-1494790108755-2616b612b3fd?w=150&h=150&fit=crop&crop=face',
      'isAllowed': true,
      'registeredDate': '12/01/2024',
    },
    {
      'id': '3',
      'name': 'Pedro Costa',
      'surname': 'Costa',
      'email': 'pedro.costa@email.com',
      'photo': 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150&h=150&fit=crop&crop=face',
      'isAllowed': false,
      'registeredDate': '10/01/2024',
    },
    {
      'id': '4',
      'name': 'Ana Oliveira',
      'surname': 'Oliveira',
      'email': 'ana.oliveira@email.com',
      'photo': 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=150&h=150&fit=crop&crop=face',
      'isAllowed': true,
      'registeredDate': '08/01/2024',
    },
  ];

  void _toggleMemberStatus(int index) {
    setState(() {
      _registeredMembers[index]['isAllowed'] = !_registeredMembers[index]['isAllowed'];
    });
    
    // Show feedback to user
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          _registeredMembers[index]['isAllowed'] 
            ? '${_registeredMembers[index]['name']} pode deixar mensagens'
            : '${_registeredMembers[index]['name']} não pode deixar mensagens',
        ),
        backgroundColor: _registeredMembers[index]['isAllowed'] 
          ? Colors.green 
          : Colors.orange,
        duration: const Duration(seconds: 2),
      ),
    );
  }

  void _deleteMember(int index) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Remover Visitante'),
        content: Text(
          'Deseja remover ${_registeredMembers[index]['name']} ${_registeredMembers[index]['surname']} dos visitantes permitidos?',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancelar'),
          ),
          ElevatedButton(
            onPressed: () {
              setState(() {
                _registeredMembers.removeAt(index);
              });
              Navigator.pop(context);
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(
                  content: Text('Visitante removido com sucesso'),
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

  void _addNewMember() async {
    final result = await showDialog<Map<String, dynamic>>(
      context: context,
      builder: (context) => const AddVisitorDialog(),
    );

    if (result != null) {
      setState(() {
        _registeredMembers.add({
          'id': DateTime.now().millisecondsSinceEpoch.toString(),
          'name': result['name'],
          'surname': result['surname'],
          'email': result['email'],
          'photo': result['photo'], // This will be the selected image path
          'isAllowed': true,
          'registeredDate': DateTime.now().day.toString().padLeft(2, '0') + 
                           '/' + DateTime.now().month.toString().padLeft(2, '0') + 
                           '/' + DateTime.now().year.toString(),
        });
      });

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('${result['name']} ${result['surname']} adicionado com sucesso!'),
            backgroundColor: Colors.green,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return BaseScreenWidget(
      title: 'Membros Registrados',
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            // Header with count
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.purple.shade50,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: Colors.purple.shade200),
              ),
              child: Row(
                children: [
                  Icon(
                    Icons.people,
                    color: Colors.purple.shade600,
                    size: 32,
                  ),
                  const SizedBox(width: 12),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Visitantes Permitidos',
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                          color: Colors.purple.shade800,
                        ),
                      ),
                      Text(
                        '${_registeredMembers.length} visitante(s) registrado(s)',
                        style: TextStyle(
                          fontSize: 14,
                          color: Colors.purple.shade600,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),

            // Members List
            Expanded(
              child: _registeredMembers.isEmpty
                  ? Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(
                            Icons.people_outline,
                            size: 64,
                            color: Colors.grey.shade400,
                          ),
                          const SizedBox(height: 16),
                          Text(
                            'Nenhum visitante registrado',
                            style: TextStyle(
                              fontSize: 18,
                              color: Colors.grey.shade600,
                            ),
                          ),
                        ],
                      ),
                    )
                  : ListView.builder(
                      itemCount: _registeredMembers.length,
                      itemBuilder: (context, index) {
                        final member = _registeredMembers[index];
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
                                // Member Photo
                                Container(
                                  width: 60,
                                  height: 60,
                                  decoration: BoxDecoration(
                                    shape: BoxShape.circle,
                                    border: Border.all(
                                      color: member['isAllowed'] 
                                        ? Colors.green.shade300
                                        : Colors.grey.shade300,
                                      width: 2,
                                    ),
                                  ),
                                  child: ClipOval(
                                    child: member['photo'].startsWith('http')
                                        ? Image.network(
                                            member['photo'],
                                            fit: BoxFit.cover,
                                            errorBuilder: (context, error, stackTrace) {
                                              return Container(
                                                color: Colors.grey.shade200,
                                                child: Icon(
                                                  Icons.person,
                                                  color: Colors.grey.shade400,
                                                  size: 30,
                                                ),
                                              );
                                            },
                                          )
                                        : Container(
                                            color: Colors.grey.shade200,
                                            child: Icon(
                                              Icons.person,
                                              color: Colors.grey.shade400,
                                              size: 30,
                                            ),
                                          ),
                                  ),
                                ),
                                const SizedBox(width: 16),
                                
                                // Member Info
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        '${member['name']} ${member['surname']}',
                                        style: const TextStyle(
                                          fontSize: 16,
                                          fontWeight: FontWeight.bold,
                                        ),
                                      ),
                                      const SizedBox(height: 4),
                                      Text(
                                        member['email'],
                                        style: TextStyle(
                                          fontSize: 14,
                                          color: Colors.grey.shade600,
                                        ),
                                      ),
                                      const SizedBox(height: 4),
                                      Text(
                                        'Registrado em: ${member['registeredDate']}',
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
                                      value: member['isAllowed'],
                                      onChanged: (value) => _toggleMemberStatus(index),
                                      activeColor: Colors.green,
                                    ),
                                  ],
                                ),
                                
                                // Delete Button
                                IconButton(
                                  onPressed: () => _deleteMember(index),
                                  icon: const Icon(
                                    Icons.close,
                                    color: Colors.red,
                                    size: 20,
                                  ),
                                  tooltip: 'Remover visitante',
                                ),
                              ],
                            ),
                          ),
                        );
                      },
                    ),
            ),

            // Add Member Button (bottom right)
            Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                ElevatedButton.icon(
                  onPressed: _addNewMember,
                  icon: const Icon(Icons.add),
                  label: const Text('Adicionar Visitante'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.purple,
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
    );
  }
} 