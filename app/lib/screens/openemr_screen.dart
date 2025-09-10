import 'package:flutter/material.dart';
import '../services/openemr_service.dart';
import '../models/patient.dart';
import '../models/encounter.dart';
import '../utils/constants.dart';
import 'package:url_launcher/url_launcher.dart';

class OpenEMRScreen extends StatefulWidget {
  const OpenEMRScreen({super.key});

  @override
  State<OpenEMRScreen> createState() => _OpenEMRScreenState();
}

class _OpenEMRScreenState extends State<OpenEMRScreen> {
  final OpenEMRService _openemrService = OpenEMRService();
  bool _isConnected = false;
  bool _isLoading = false;
  String? _connectionStatus;
  List<Patient> _patients = [];
  Patient? _selectedPatient;
  List<Encounter> _encounters = [];
  Encounter? _selectedEncounter;
  final TextEditingController _searchController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _checkConnectionStatus();
  }

  Future<void> _checkConnectionStatus() async {
    setState(() => _isLoading = true);
    try {
      final isConnected = await _openemrService.checkConnection();
      setState(() {
        _isConnected = isConnected;
        _connectionStatus = isConnected ? 'Connected to OpenEMR' : 'Not connected';
      });
    } catch (e) {
      setState(() {
        _isConnected = false;
        _connectionStatus = 'Connection error: $e';
      });
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _connectToOpenEMR() async {
    setState(() => _isLoading = true);
    try {
      final authorizeUrl = await _openemrService.getAuthorizeUrl();
      if (authorizeUrl != null) {
        // Launch SMART-on-FHIR authorize URL
        await launchUrl(Uri.parse(authorizeUrl), mode: LaunchMode.externalApplication);
        _showConnectionDialog();
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Failed to connect: $e')),
      );
    } finally {
      setState(() => _isLoading = false);
    }
  }

  void _showConnectionDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Connecting to OpenEMR'),
        content: const Text(
          'Complete the authentication in your browser, then return here and click "Check Connection" to verify.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(context);
              _checkConnectionStatus();
            },
            child: const Text('Check Connection'),
          ),
        ],
      ),
    );
  }

  Future<void> _searchPatients() async {
    if (_searchController.text.trim().isEmpty) return;
    
    setState(() => _isLoading = true);
    try {
      final patients = await _openemrService.searchPatients(_searchController.text);
      setState(() {
        _patients = patients;
        _selectedPatient = null;
        _encounters = [];
        _selectedEncounter = null;
      });
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Failed to search patients: $e')),
      );
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _loadPatientEncounters(Patient patient) async {
    setState(() {
      _selectedPatient = patient;
      _isLoading = true;
    });
    
    try {
      final encounters = await _openemrService.getPatientEncounters(patient.id);
      setState(() {
        _encounters = encounters;
        _selectedEncounter = null;
      });
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Failed to load encounters: $e')),
      );
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _createNewEncounter() async {
    if (_selectedPatient == null) return;
    
    setState(() => _isLoading = true);
    try {
      final encounter = await _openemrService.createEncounter(_selectedPatient!.id);
      if (encounter != null) {
        setState(() {
          _encounters.insert(0, encounter);
          _selectedEncounter = encounter;
        });
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('New encounter created successfully')),
        );
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Failed to create encounter: $e')),
      );
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _startTranscriptionWithContext() async {
    if (_selectedPatient == null || _selectedEncounter == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please select a patient and encounter first')),
      );
      return;
    }

    // Show success message with patient context
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          'Transcription ready for:\n'
          'Patient: ${_selectedPatient!.fullName}\n'
          'Encounter: ${_selectedEncounter!.type} - ${_selectedEncounter!.date}\n\n'
          'This will integrate with the main transcription interface.',
        ),
        backgroundColor: Constants.successColor,
        duration: const Duration(seconds: 4),
      ),
    );
    
    // For now, just go back to main screen where user can use transcription
    Navigator.of(context).pop();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('OpenEMR Integration'),
        backgroundColor: Constants.primaryColor,
        foregroundColor: Colors.white,
      ),
      body: Padding(
        padding: const EdgeInsets.all(Constants.padding),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Connection Status
            Card(
              child: Padding(
                padding: const EdgeInsets.all(Constants.padding),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Icon(
                          _isConnected ? Icons.check_circle : Icons.error,
                          color: _isConnected ? Constants.successColor : Constants.errorColor,
                        ),
                        const SizedBox(width: 8),
                        Text(
                          'Connection Status',
                          style: Theme.of(context).textTheme.titleMedium?.copyWith(
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Text(_connectionStatus ?? 'Checking...'),
                    const SizedBox(height: 16),
                    Row(
                      children: [
                        if (!_isConnected)
                          ElevatedButton(
                            onPressed: _isLoading ? null : _connectToOpenEMR,
                            child: _isLoading 
                              ? const SizedBox(
                                  width: 16,
                                  height: 16,
                                  child: CircularProgressIndicator(strokeWidth: 2),
                                )
                              : const Text('Connect to OpenEMR'),
                          ),
                        const SizedBox(width: 8),
                        TextButton(
                          onPressed: _checkConnectionStatus,
                          child: const Text('Refresh Status'),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),

            if (_isConnected) ...[
              const SizedBox(height: 16),
              
              // Patient Search
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(Constants.padding),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Patient Search',
                        style: Theme.of(context).textTheme.titleMedium?.copyWith(
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 16),
                      Row(
                        children: [
                          Expanded(
                            child: TextField(
                              controller: _searchController,
                              decoration: const InputDecoration(
                                hintText: 'Enter patient name or ID',
                                border: OutlineInputBorder(),
                              ),
                              onSubmitted: (_) => _searchPatients(),
                            ),
                          ),
                          const SizedBox(width: 8),
                          ElevatedButton(
                            onPressed: _isLoading ? null : _searchPatients,
                            child: const Text('Search'),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ),

              // Patient List
              if (_patients.isNotEmpty) ...[
                const SizedBox(height: 16),
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(Constants.padding),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Patients (${_patients.length})',
                          style: Theme.of(context).textTheme.titleMedium?.copyWith(
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                        const SizedBox(height: 8),
                        ...(_patients.take(10).map((patient) => ListTile(
                          title: Text('${patient.firstName} ${patient.lastName}'),
                          subtitle: Text('DOB: ${patient.dateOfBirth} • ID: ${patient.id}'),
                          trailing: _selectedPatient?.id == patient.id 
                            ? const Icon(Icons.check_circle, color: Constants.successColor)
                            : null,
                          onTap: () => _loadPatientEncounters(patient),
                        )).toList()),
                      ],
                    ),
                  ),
                ),
              ],

              // Encounters Section
              if (_selectedPatient != null) ...[
                const SizedBox(height: 16),
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(Constants.padding),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Text(
                              'Encounters for ${_selectedPatient!.firstName} ${_selectedPatient!.lastName}',
                              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            ElevatedButton(
                              onPressed: _isLoading ? null : _createNewEncounter,
                              child: const Text('New Encounter'),
                            ),
                          ],
                        ),
                        const SizedBox(height: 16),
                        if (_encounters.isEmpty && !_isLoading)
                          const Text('No encounters found. Create a new encounter to start transcribing.')
                        else
                          ...(_encounters.map((encounter) => ListTile(
                            title: Text('${encounter.type} - ${encounter.date}'),
                            subtitle: Text('Status: ${encounter.status}'),
                            trailing: _selectedEncounter?.id == encounter.id 
                              ? const Icon(Icons.check_circle, color: Constants.successColor)
                              : null,
                            onTap: () => setState(() => _selectedEncounter = encounter),
                          )).toList()),
                      ],
                    ),
                  ),
                ),
              ],

              // Start Transcription
              if (_selectedPatient != null && _selectedEncounter != null) ...[
                const SizedBox(height: 16),
                Card(
                  color: Constants.primaryColor.withOpacity(0.1),
                  child: Padding(
                    padding: const EdgeInsets.all(Constants.padding),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Ready to Start Transcription',
                          style: Theme.of(context).textTheme.titleMedium?.copyWith(
                            fontWeight: FontWeight.bold,
                            color: Constants.primaryColor,
                          ),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          'Patient: ${_selectedPatient!.firstName} ${_selectedPatient!.lastName}\n'
                          'Encounter: ${_selectedEncounter!.type} - ${_selectedEncounter!.date}',
                        ),
                        const SizedBox(height: 16),
                        ElevatedButton.icon(
                          onPressed: _startTranscriptionWithContext,
                          icon: const Icon(Icons.mic),
                          label: const Text('Start Transcription'),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: Constants.primaryColor,
                            foregroundColor: Colors.white,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ],
          ],
        ),
      ),
    );
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }
}
