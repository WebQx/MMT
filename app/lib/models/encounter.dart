class Encounter {
  final String id;
  final String patientId;
  final String status;
  final String type;
  final String date;
  final String? endDate;
  final String? location;
  final String? provider;

  Encounter({
    required this.id,
    required this.patientId,
    required this.status,
    required this.type,
    required this.date,
    this.endDate,
    this.location,
    this.provider,
  });

  bool get isActive => status == 'in-progress' || status == 'arrived';
  
  factory Encounter.fromFhir(Map<String, dynamic> fhirResource) {
    final subject = fhirResource['subject'] as Map<String, dynamic>?;
    final patientRef = subject?['reference'] as String? ?? '';
    final patientId = patientRef.replaceAll('Patient/', '');
    
    final period = fhirResource['period'] as Map<String, dynamic>? ?? {};
    final startDate = period['start'] as String? ?? DateTime.now().toIso8601String();
    final endDate = period['end'] as String?;
    
    final type = _extractType(fhirResource['type'] as List<dynamic>?);
    final location = _extractLocation(fhirResource['location'] as List<dynamic>?);
    final provider = _extractProvider(fhirResource['participant'] as List<dynamic>?);

    return Encounter(
      id: fhirResource['id'] as String,
      patientId: patientId,
      status: fhirResource['status'] as String? ?? 'unknown',
      type: type,
      date: _formatDate(startDate),
      endDate: endDate != null ? _formatDate(endDate) : null,
      location: location,
      provider: provider,
    );
  }

  static String _extractType(List<dynamic>? types) {
    if (types == null || types.isEmpty) return 'General Visit';
    
    final type = types.first as Map<String, dynamic>;
    final coding = type['coding'] as List<dynamic>? ?? [];
    
    if (coding.isNotEmpty) {
      final code = coding.first as Map<String, dynamic>;
      return code['display'] as String? ?? 'General Visit';
    }
    
    return type['text'] as String? ?? 'General Visit';
  }

  static String? _extractLocation(List<dynamic>? locations) {
    if (locations == null || locations.isEmpty) return null;
    
    final location = locations.first as Map<String, dynamic>;
    final locationRef = location['location'] as Map<String, dynamic>?;
    return locationRef?['display'] as String?;
  }

  static String? _extractProvider(List<dynamic>? participants) {
    if (participants == null || participants.isEmpty) return null;
    
    for (final participant in participants) {
      final p = participant as Map<String, dynamic>;
      final type = p['type'] as List<dynamic>? ?? [];
      
      // Look for primary performer/doctor
      for (final t in type) {
        final coding = (t as Map<String, dynamic>)['coding'] as List<dynamic>? ?? [];
        for (final c in coding) {
          final code = (c as Map<String, dynamic>)['code'] as String?;
          if (code == 'PPRF' || code == 'PRF') {
            final individual = p['individual'] as Map<String, dynamic>?;
            return individual?['display'] as String?;
          }
        }
      }
    }
    
    return null;
  }

  static String _formatDate(String isoDate) {
    try {
      final date = DateTime.parse(isoDate);
      return '${date.month}/${date.day}/${date.year} ${_formatTime(date)}';
    } catch (e) {
      return isoDate;
    }
  }

  static String _formatTime(DateTime date) {
    final hour = date.hour == 0 ? 12 : (date.hour > 12 ? date.hour - 12 : date.hour);
    final minute = date.minute.toString().padLeft(2, '0');
    final ampm = date.hour >= 12 ? 'PM' : 'AM';
    return '$hour:$minute $ampm';
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'patientId': patientId,
      'status': status,
      'type': type,
      'date': date,
      'endDate': endDate,
      'location': location,
      'provider': provider,
    };
  }

  factory Encounter.fromJson(Map<String, dynamic> json) {
    return Encounter(
      id: json['id'] as String,
      patientId: json['patientId'] as String,
      status: json['status'] as String,
      type: json['type'] as String,
      date: json['date'] as String,
      endDate: json['endDate'] as String?,
      location: json['location'] as String?,
      provider: json['provider'] as String?,
    );
  }
}
