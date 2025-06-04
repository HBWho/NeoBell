class DeliveryService {
  Future<List<Map<String, String>>> getDeliveryActivities() async {
    await Future.delayed(Duration(milliseconds: 500)); // Simula carregamento

    return [
      {
        'name': 'Ana Luisa Delivery',
        'message': 'Ana Luisa is in your house',
      },
      {
        'name': 'Ana Luisa Delivery',
        'message': 'Ana Luisa is interacting with NeoBell',
      },
      {
        'name': 'Ana Luisa Delivery',
        'message': 'The delivery was successfully completed',
      },
      {
        'name': 'The BOX number: PN123456789BR',
        'message': 'The delivery has been completed',
      },
    ];
  }
}
