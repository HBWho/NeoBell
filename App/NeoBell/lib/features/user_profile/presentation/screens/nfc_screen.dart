import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/common/widgets/base_screen_widget.dart';
import '../../../../core/utils/show_snackbar.dart';
import '../cubit/user_profile_cubit.dart';
import '../widgets/nfc_scan_dialog.dart';

class NfcScreen extends StatefulWidget {
  const NfcScreen({super.key});

  @override
  State<NfcScreen> createState() => _NfcScreenState();
}

class _NfcScreenState extends State<NfcScreen> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  String? _scannedTagId;

  @override
  void initState() {
    super.initState();
    final userProfileCubit = context.read<UserProfileCubit>();
    if (userProfileCubit.state is! UserProfileLoaded) {
      userProfileCubit.loadProfile();
      userProfileCubit.loadNfcTags();
    } else if ((userProfileCubit.state as UserProfileLoaded)
        .profile
        .nfcTags
        .isEmpty) {
      userProfileCubit.loadNfcTags();
    }
  }

  @override
  void dispose() {
    _nameController.dispose();
    super.dispose();
  }

  Future<void> _scanNfcTag() async {
    final result = await showDialog<String>(
      context: context,
      barrierDismissible: false,
      builder: (context) => const NfcScanDialog(),
    );

    if (result != null && mounted) {
      setState(() => _scannedTagId = result);
    }
  }

  Future<void> _registerTag() async {
    if (_scannedTagId == null || !_formKey.currentState!.validate()) return;

    await context.read<UserProfileCubit>().registerNfcTag(
      _scannedTagId!,
      _nameController.text.trim(),
    );
  }

  @override
  Widget build(BuildContext context) {
    return BaseScreenWidget(
      title: 'NFC',
      actions: [
        IconButton(
          icon: const Icon(Icons.refresh),
          onPressed: () {
            context.read<UserProfileCubit>().loadNfcTags();
          },
        ),
      ],
      body: BlocConsumer<UserProfileCubit, UserProfileState>(
        listener: (context, state) {
          if (state is UserProfileError) {
            showSnackBar(
              context,
              message: 'Erro ao registrar tag: ${state.message}',
              isError: true,
            );
          }
          if (state is UserProfileLoaded && state.message != null) {
            showSnackBar(context, message: state.message!, isSucess: true);
          }
        },
        builder: (context, state) {
          if (state is UserProfileLoading) {
            return const Center(child: CircularProgressIndicator());
          }
          if (state is UserProfileLoaded) {
            return SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Form(
                key: _formKey,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    NFCListWidgets(state),
                    const SizedBox(height: 16),
                    const Divider(),
                    const SizedBox(height: 16),
                    const Text(
                      'Register a new NFC Tag',
                      textAlign: TextAlign.center,
                      style: TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 16),
                    TextFormField(
                      controller: _nameController,
                      decoration: const InputDecoration(
                        labelText: 'Friendly Name',
                        hintText: 'E.g. Main Tag, Secondary Tag',
                      ),
                      validator: (value) {
                        if (value == null || value.trim().isEmpty) {
                          return 'Please enter a friendly name for the tag.';
                        }
                        return null;
                      },
                    ),
                    const SizedBox(height: 24),
                    ElevatedButton.icon(
                      onPressed: _scanNfcTag,
                      icon: const Icon(Icons.nfc),
                      label: Text(
                        _scannedTagId == null ? 'Scan NFC Tag' : 'Scan Again',
                      ),
                    ),
                    if (_scannedTagId != null) ...[
                      const SizedBox(height: 16),
                      Card(
                        child: ListTile(
                          leading: const Icon(
                            Icons.check_circle,
                            color: Colors.green,
                          ),
                          title: const Text('NFC Tag Detected'),
                          subtitle: Text(_scannedTagId!),
                        ),
                      ),
                      const SizedBox(height: 24),
                      ElevatedButton(
                        onPressed: _registerTag,
                        child: const Text('Register Tag'),
                      ),
                    ],
                  ],
                ),
              ),
            );
          }
          return Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Text('Failed to load profile'),
                ElevatedButton(
                  onPressed: () {
                    context.read<UserProfileCubit>().loadProfile();
                  },
                  child: const Text('Retry'),
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}

class NFCListWidgets extends StatelessWidget {
  final UserProfileLoaded state;
  const NFCListWidgets(this.state, {super.key});

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'NFC Tags',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 16),
            if (state.profile.nfcTags.isEmpty)
              const Text('No NFC tags registered')
            else
              ListView.builder(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                itemCount: state.profile.nfcTags.length,
                itemBuilder: (context, index) {
                  final tag = state.profile.nfcTags[index];
                  return ListTile(
                    title: Text(
                      tag.tagFriendlyName.isEmpty
                          ? 'Tag ${index + 1}'
                          : tag.tagFriendlyName,
                    ),
                    subtitle: Text(tag.nfcId),
                    trailing: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        IconButton(
                          icon: const Icon(Icons.edit),
                          onPressed: () async {
                            String? newFriendlyName;
                            await showDialog(
                              context: context,
                              builder:
                                  (context) => AlertDialog(
                                    title: const Text(
                                      'Edit NFC Tag friendly name',
                                    ),
                                    content: TextField(
                                      onChanged: (value) {
                                        newFriendlyName = value;
                                      },
                                      decoration: const InputDecoration(
                                        hintText: 'Enter new friendly name',
                                      ),
                                    ),
                                    actions: [
                                      TextButton(
                                        onPressed: () {
                                          newFriendlyName = null;
                                          context.pop();
                                        },
                                        child: const Text('Cancel'),
                                      ),
                                      TextButton(
                                        onPressed: () => context.pop(),
                                        child: const Text('Edit'),
                                      ),
                                    ],
                                  ),
                            );

                            if (newFriendlyName != null && context.mounted) {
                              context.read<UserProfileCubit>().updateNfcTag(
                                tagId: tag.nfcId,
                                friendlyName: newFriendlyName!,
                              );
                            }
                          },
                        ),
                        IconButton(
                          icon: const Icon(Icons.delete),
                          onPressed: () async {
                            final confirmed = await showDialog<bool>(
                              context: context,
                              builder:
                                  (context) => AlertDialog(
                                    title: const Text('Remove NFC Tag'),
                                    content: const Text(
                                      'Are you sure you want to remove this NFC tag?',
                                    ),
                                    actions: [
                                      TextButton(
                                        onPressed:
                                            () => Navigator.pop(context, false),
                                        child: const Text('Cancel'),
                                      ),
                                      TextButton(
                                        onPressed:
                                            () => Navigator.pop(context, true),
                                        child: const Text('Remove'),
                                      ),
                                    ],
                                  ),
                            );

                            if (confirmed == true && context.mounted) {
                              context.read<UserProfileCubit>().removeNfcTag(
                                tag.nfcId,
                              );
                            }
                          },
                        ),
                      ],
                    ),
                  );
                },
              ),
          ],
        ),
      ),
    );
  }
}
