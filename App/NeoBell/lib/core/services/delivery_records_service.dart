class DeliveryRecordsService {
  Future<List<Map<String, String>>> getAllDeliveryRecords() async {
    await Future.delayed(const Duration(milliseconds: 400)); // Simula carregamento

    return [
      {
        'code': 'OD112233445BR',
        'type': 'Makeup',
        'description': 'Amazon delivery',
      },
      {
        'code': 'PN123456789BR',
        'type': 'Notebook',
        'description': 'Shopee delivery',
      },
      {
        'code': 'LB987654321BR',
        'type': 'Smartphone',
        'description': 'Aliexpress delivery',
      },
    ];
  }
}
