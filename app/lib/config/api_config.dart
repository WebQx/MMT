// BASE_URL is provided via --dart-define at build/run time.
// Example: --dart-define=BASE_URL=https://transcribe.example.com
const String BASE_URL = String.fromEnvironment('BASE_URL', defaultValue: 'http://localhost:8000');
