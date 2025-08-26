class TranscriptionResult {
  final String id;
  final String text;
  final String language;
  final double confidence;
  final DateTime timestamp;

  TranscriptionResult({
    required this.id,
    required this.text,
    required this.language,
    required this.confidence,
    required this.timestamp,
  });

  factory TranscriptionResult.fromJson(Map<String, dynamic> json) {
    return TranscriptionResult(
      id: json['id'] as String,
      text: json['text'] as String,
      language: json['language'] as String,
      confidence: (json['confidence'] as num).toDouble(),
      timestamp: DateTime.parse(json['timestamp'] as String),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'text': text,
      'language': language,
      'confidence': confidence,
      'timestamp': timestamp.toIso8601String(),
    };
  }

  @override
  String toString() {
    return 'TranscriptionResult{id: $id, text: $text, language: $language, confidence: $confidence, timestamp: $timestamp}';
  }
}