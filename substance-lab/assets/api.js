/* =====================================================================
   AION API client — shared by index.html (login) and dashboard.html
   Vanilla JS, no build step. Talks to the finals-backend FastAPI service.
   ===================================================================== */
(function (global) {
  'use strict';

  // Base URL is overridable: set window.AION_API_BASE before this script loads.
  var API_BASE = global.AION_API_BASE || 'http://localhost:8001/api/v1';

  var KEY_ACCESS = 'aion_access_token';
  var KEY_REFRESH = 'aion_refresh_token';

  function getAccess() { return localStorage.getItem(KEY_ACCESS); }
  function getRefresh() { return localStorage.getItem(KEY_REFRESH); }
  function setTokens(t) {
    if (t && t.access_token) localStorage.setItem(KEY_ACCESS, t.access_token);
    if (t && t.refresh_token) localStorage.setItem(KEY_REFRESH, t.refresh_token);
  }
  function clearTokens() {
    localStorage.removeItem(KEY_ACCESS);
    localStorage.removeItem(KEY_REFRESH);
  }
  function isAuthed() { return !!getAccess(); }

  // Decode a JWT payload (org_id, role, email, permissions) — display only.
  function parseJwt(token) {
    try {
      var base = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
      var json = decodeURIComponent(atob(base).split('').map(function (c) {
        return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
      }).join(''));
      return JSON.parse(json);
    } catch (e) { return {}; }
  }

  function claims() { var t = getAccess(); return t ? parseJwt(t) : {}; }

  // --- Auth: login uses OAuth2 form-encoding (username = email OR username) ---
  function login(identifier, password) {
    var body = new URLSearchParams();
    body.set('username', identifier);
    body.set('password', password);
    return fetch(API_BASE + '/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: body.toString()
    }).then(function (res) {
      return res.json().then(function (data) {
        if (!res.ok) {
          var msg = (data && (data.message || data.detail)) || 'Login failed';
          throw new Error(typeof msg === 'string' ? msg : 'Login failed');
        }
        setTokens(data);
        return data;
      });
    });
  }

  // Register uses JSON.
  function register(payload) {
    return fetch(API_BASE + '/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    }).then(function (res) {
      return res.json().then(function (data) {
        if (!res.ok) throw new Error((data && (data.message || data.detail)) || 'Registration failed');
        setTokens(data);
        return data;
      });
    });
  }

  function refresh() {
    var rt = getRefresh();
    if (!rt) return Promise.reject(new Error('No refresh token'));
    return fetch(API_BASE + '/auth/refresh?refresh_token=' + encodeURIComponent(rt), {
      method: 'POST'
    }).then(function (res) {
      if (!res.ok) throw new Error('Refresh failed');
      return res.json();
    }).then(function (data) { setTokens(data); return data; });
  }

  function logout(redirect) {
    clearTokens();
    if (redirect !== false) global.location.href = 'index.html';
  }

  // Authenticated GET/POST with a single automatic refresh-and-retry on 401.
  function authFetch(path, opts, _retried) {
    opts = opts || {};
    var headers = Object.assign({}, opts.headers || {});
    var tok = getAccess();
    if (tok) headers['Authorization'] = 'Bearer ' + tok;
    return fetch(API_BASE + path, Object.assign({}, opts, { headers: headers }))
      .then(function (res) {
        if (res.status === 401 && !_retried && getRefresh()) {
          return refresh()
            .then(function () { return authFetch(path, opts, true); })
            .catch(function () { logout(); throw new Error('Session expired'); });
        }
        return res;
      });
  }

  function get(path) {
    return authFetch(path).then(function (res) {
      if (!res.ok) throw new Error('GET ' + path + ' → ' + res.status);
      return res.json();
    });
  }

  // Redirect to the landing page (and open the login modal) if not signed in.
  function requireAuth() {
    if (!isAuthed()) { global.location.href = 'index.html?auth=1'; return false; }
    return true;
  }

  global.AION = {
    API_BASE: API_BASE,
    login: login,
    register: register,
    refresh: refresh,
    logout: logout,
    get: get,
    authFetch: authFetch,
    isAuthed: isAuthed,
    requireAuth: requireAuth,
    claims: claims,
    endpoints: {
      oii: '/intelligence/index',
      trends: '/intelligence/trends',
      diseases: '/diseases/scan',
      brainMap: '/mri/brain-map',
      bottlenecks: '/mri/bottlenecks',
      departments: '/graph/departments',
      risks: '/advisor/risks',
      briefing: '/advisor/briefing/latest',
      entropy: '/decay/entropy',
      decay: '/decay/report'
    }
  };
})(window);
