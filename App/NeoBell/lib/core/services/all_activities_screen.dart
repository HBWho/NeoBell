class NotificationService {
  Future<List<Map<String, String>>> getAllNotifications() async {
    await Future.delayed(const Duration(milliseconds: 500)); // simula carregamento

    return [
      {
        'name': 'Ana Luisa Delivery',
        'message': 'Ana Luisa is in your house',
        'date': '22/05',
      },
      {
        'name': 'Ana Luisa Delivery',
        'message': 'Ana Luisa is interacting with NeoBell',
        'date': '22/05',
      },
      {
        'name': 'Ana Luisa Delivery',
        'message': 'The delivery was successfully completed',
        'date': '22/05',
      },
      {
        'name': 'The BOX number: PN123456789BR',
        'message': 'The delivery has been completed',
        'date': '13/05',
      },
      {
        'name': 'Alexei Visitor',
        'message': 'Alexei left a video message',
        'date': '20/03',
      },
      {
        'name': 'Luis Visitor',
        'message': 'Luis left a message',
        'date': '17/03',
      },
      {
        'name': 'Pedro Visitor',
        'message': 'Pedro left a video message and message',
        'date': '',
      },
    ];
  }
}
