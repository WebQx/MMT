class Patient {
  final String id;
  final String firstName;
  final String lastName;
  final String? dateOfBirth;
  final String? gender;
  final String? phone;
  final String? email;
  final String? address;

  Patient({
    required this.id,
    required this.firstName,
    required this.lastName,
    this.dateOfBirth,
    this.gender,
    this.phone,
    this.email,
    this.address,
  });

  String get fullName => '$firstName $lastName';
  
  factory Patient.fromFhir(Map<String, dynamic> fhirResource) {
    final name = _extractName(fhirResource['name'] as List<dynamic>?);
    final telecom = fhirResource['telecom'] as List<dynamic>? ?? [];
    final address = fhirResource['address'] as List<dynamic>? ?? [];
    
    String? phone;
    String? email;
    
    for (final contact in telecom) {
      final system = contact['system'] as String?;
      final value = contact['value'] as String?;
      if (system == 'phone' && phone == null) {
        phone = value;
      } else if (system == 'email' && email == null) {
        email = value;
      }
    }
    
    String? addressStr;
    if (address.isNotEmpty) {
      final addr = address.first as Map<String, dynamic>;
      final line = addr['line'] as List<dynamic>? ?? [];
      final city = addr['city'] as String? ?? '';
      final state = addr['state'] as String? ?? '';
      final postalCode = addr['postalCode'] as String? ?? '';
      
      addressStr = '${line.isNotEmpty ? line.first : ''} $city $state $postalCode'.trim();
      if (addressStr.isEmpty) addressStr = null;
    }

    return Patient(
      id: fhirResource['id'] as String,
      firstName: name['given'] ?? 'Unknown',
      lastName: name['family'] ?? 'Unknown',
      dateOfBirth: fhirResource['birthDate'] as String?,
      gender: fhirResource['gender'] as String?,
      phone: phone,
      email: email,
      address: addressStr,
    );
  }

  static Map<String, String?> _extractName(List<dynamic>? names) {
    if (names == null || names.isEmpty) {
      return {'given': null, 'family': null};
    }
    
    final name = names.first as Map<String, dynamic>;
    final given = name['given'] as List<dynamic>? ?? [];
    final family = name['family'] as String?;
    
    return {
      'given': given.isNotEmpty ? given.first as String : null,
      'family': family,
    };
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'firstName': firstName,
      'lastName': lastName,
      'dateOfBirth': dateOfBirth,
      'gender': gender,
      'phone': phone,
      'email': email,
      'address': address,
    };
  }

  factory Patient.fromJson(Map<String, dynamic> json) {
    return Patient(
      id: json['id'] as String,
      firstName: json['firstName'] as String,
      lastName: json['lastName'] as String,
      dateOfBirth: json['dateOfBirth'] as String?,
      gender: json['gender'] as String?,
      phone: json['phone'] as String?,
      email: json['email'] as String?,
      address: json['address'] as String?,
    );
  }
}
