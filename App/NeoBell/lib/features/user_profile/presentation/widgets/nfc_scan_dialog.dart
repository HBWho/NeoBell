import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:logger/logger.dart';
import 'package:nfc_manager/nfc_manager.dart';
import 'package:nfc_manager/nfc_manager_android.dart';

class NfcScanDialog extends StatefulWidget {
  const NfcScanDialog({super.key});

  @override
  State<NfcScanDialog> createState() => _NfcScanDialogState();
}

class _NfcScanDialogState extends State<NfcScanDialog> {
  final Logger _logger = Logger();
  bool _isScanning = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _startScan();
  }

  @override
  void dispose() {
    super.dispose();
    NfcManager.instance.stopSession().catchError((_) {});
  }

  Future<void> _startScan() async {
    setState(() {
      _isScanning = true;
      _error = null;
    });

    try {
      bool isAvailable = await NfcManager.instance.isAvailable();
      if (!isAvailable) {
        setState(() {
          _error = 'NFC is not supported on this device';
          _isScanning = false;
        });
        return;
      }
      await NfcManager.instance.startSession(
        pollingOptions: {...NfcPollingOption.values},
        onDiscovered: (NfcTag tag) async {
          _logger.i('Tag NFC detectada: ${tag.toString()}');
          try {
            final nfcTagAndroid = NfcTagAndroid.from(tag);
            if (nfcTagAndroid == null) {
              setState(() => _error = 'The NFC tag is not supported');
              return;
            }
            final hexId = nfcTagAndroid.id
                .map((e) => e.toRadixString(16).padLeft(2, '0'))
                .join(':');
            if (mounted) {
              Navigator.of(context).pop(hexId);
            }
          } catch (e) {
            setState(() => _error = 'Error trying to read tag: $e');
          }
        },
      );
    } on PlatformException catch (e) {
      setState(() {
        _error = '${e.message}';
        _isScanning = false;
      });
    } catch (e) {
      setState(() {
        _error = 'Error starting NFC scanner: $e';
        _isScanning = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Scanning NFC Tag'),
      content: SizedBox(
        height: 150,
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            if (_error != null) ...[
              Icon(Icons.error_outline, color: Colors.red.shade700, size: 48),
              const SizedBox(height: 16),
              Text(
                _error!,
                textAlign: TextAlign.center,
                style: TextStyle(color: Colors.red.shade700),
              ),
            ] else if (_isScanning) ...[
              const CircularProgressIndicator(),
              const SizedBox(height: 16),
              const Text(
                'Bring the NFC tag close to the device',
                textAlign: TextAlign.center,
              ),
            ],
          ],
        ),
      ),
      actions: [
        if (_error != null) ...[
          TextButton(onPressed: _startScan, child: const Text('Try Again')),
        ],
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('Cancel'),
        ),
      ],
    );
  }
}
