// Rename to config.js and place alongside index.html to set production API base.
// You can also copy its contents inline in <head> before script.js.
// Highest precedence after URL query parameters (?api=) for selecting backend.
// Example Railway backend URL shown below.

window.__MMT_CONFIG = {
  API_BASE_URL: 'https://your-railway-backend.example', // e.g. https://mmt-prod.up.railway.app
  // Future options could include feature flags, theme, etc.
};
