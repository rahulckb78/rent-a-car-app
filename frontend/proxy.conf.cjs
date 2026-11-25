// The browser only talks to the Angular dev server; /api (including /api/auth) is proxied to FastAPI.
// Same origin in dev and prod means no CORS and first-party cookies. dev.py sets API_PORT.
module.exports = {
  '/api': { target: `http://localhost:${process.env.API_PORT || 8000}`, secure: false },
};
