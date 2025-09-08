class I18n {
  static const Map<String, Map<String, String>> _t = {
    'en': {
      'email': 'Email',
      'password': 'Password',
      'sign_in': 'Sign in with email',
      'or': 'or',
      'sso': 'Sign in with SSO',
      'guest': 'Continue as Guest',
      'sign_up': 'Sign Up',
      'forgot': 'Forgot Password?',
      'language': 'Language:',
    },
    'es': {
      'email': 'Correo',
      'password': 'Contraseña',
      'sign_in': 'Iniciar sesión con correo',
      'or': 'o',
      'sso': 'Iniciar sesión con SSO',
      'guest': 'Continuar como invitado',
      'sign_up': 'Crear cuenta',
      'forgot': '¿Olvidó su contraseña?',
      'language': 'Idioma:',
    },
    'zh': {
      'email': '邮箱',
      'password': '密码',
      'sign_in': '使用邮箱登录',
      'or': '或',
      'sso': '使用单点登录',
      'guest': '以游客身份继续',
      'sign_up': '创建账户',
      'forgot': '忘记密码？',
      'language': '语言：',
    },
    'hi': {
      'email': 'ईमेल',
      'password': 'पासवर्ड',
      'sign_in': 'ईमेल से साइन इन',
      'or': 'या',
      'sso': 'SSO से साइन इन',
      'guest': 'अतिथि के रूप में जारी रखें',
      'sign_up': 'खाता बनाएं',
      'forgot': 'पासवर्ड भूल गए?',
      'language': 'भाषा:',
    },
    'ar': {
      'email': 'البريد الإلكتروني',
      'password': 'كلمة المرور',
      'sign_in': 'تسجيل الدخول بالبريد',
      'or': 'أو',
      'sso': 'تسجيل الدخول عبر SSO',
      'guest': 'المتابعة كزائر',
      'sign_up': 'إنشاء حساب',
      'forgot': 'هل نسيت كلمة المرور؟',
      'language': 'اللغة:',
    },
  };

  static String t(String key, String lang) {
    return _t[lang]?[key] ?? _t['en']![key] ?? key;
  }
}
