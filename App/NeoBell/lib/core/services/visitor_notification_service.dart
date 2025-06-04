class VisitorNotificationService {
  Future<List<Map<String, String>>> getVisitorVideos() async {
    await Future.delayed(const Duration(milliseconds: 400)); // simula fetch

    return [
      {
        'name': 'Ana Luisa Visitor',
        'videoUrl': 'https://meubanco.com/videos/ana_luisa.mp4',
      },
      {
        'name': 'Alexei Visitor',
        'videoUrl': 'https://meubanco.com/videos/alexei.mp4',
      },
      {
        'name': 'Pedro Visitor',
        'videoUrl': 'https://meubanco.com/videos/pedro.mp4',
      },
    ];
  }
}
