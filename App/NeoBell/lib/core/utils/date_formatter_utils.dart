/// Format timestamp for display: DD/MM/YYYY HH:MM:SS
String formatFullTimestamp(DateTime timestamp) {
  return '${formatDateOnly(timestamp)} ${formatTimeOnly(timestamp)}';
}

/// Format timestamp for display: DD/MM/YYYY HH:MM
String formatShortTimestamp(DateTime timestamp) {
  return '${formatDateOnly(timestamp)} ${formatShortTimeOnly(timestamp)}';
}

/// Format date only: DD/MM/YYYY
String formatDateOnly(DateTime date) {
  final day = date.day.toString().padLeft(2, '0');
  final month = date.month.toString().padLeft(2, '0');
  final year = date.year.toString();

  return '$day/$month/$year';
}

/// Format relative time (e.g., "2h ago", "Just now")
String formatRelativeTime(DateTime timestamp) {
  final now = DateTime.now();
  final difference = now.difference(timestamp);

  if (difference.inDays > 0) {
    return '${difference.inDays}d ago';
  } else if (difference.inHours > 0) {
    return '${difference.inHours}h ago';
  } else if (difference.inMinutes > 0) {
    return '${difference.inMinutes}m ago';
  } else {
    return 'Just now';
  }
}

/// Format time (HH:MM:SS)
String formatTimeOnly(DateTime time) {
  final second = time.second.toString().padLeft(2, '0');

  return '${formatShortTimeOnly(time)}:$second';
}

/// Format short time (HH:MM)
String formatShortTimeOnly(DateTime dateTime) {
  final hour = dateTime.hour.toString().padLeft(2, '0');
  final minute = dateTime.minute.toString().padLeft(2, '0');

  return '$hour:$minute';
}

/// Parse timezone-aware timestamp from API
DateTime parseApiTimestamp(String? timestamp) {
  if (timestamp == null) return DateTime.now();
  try {
    return DateTime.parse(timestamp).toLocal();
  } catch (e) {
    return DateTime.now();
  }
}
