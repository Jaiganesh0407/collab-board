// Small fetch wrapper that attaches the JWT and redirects to /login on 401.
const API = {
  token() {
    return localStorage.getItem("cb_token");
  },
  setToken(t) {
    localStorage.setItem("cb_token", t);
  },
  clearToken() {
    localStorage.removeItem("cb_token");
  },
  async request(path, options = {}) {
    const headers = options.headers || {};
    const token = this.token();
    if (token) headers["Authorization"] = `Bearer ${token}`;
    if (options.body && !(options.body instanceof URLSearchParams)) {
      headers["Content-Type"] = "application/json";
    }
    const res = await fetch(path, { ...options, headers });
    if (res.status === 401) {
      this.clearToken();
      window.location.href = "/login";
      return null;
    }
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || "Request failed");
    }
    if (res.status === 204) return null;
    return res.json();
  },
  get(path) {
    return this.request(path);
  },
  post(path, body) {
    return this.request(path, { method: "POST", body: JSON.stringify(body) });
  },
  patch(path, body) {
    return this.request(path, { method: "PATCH", body: JSON.stringify(body) });
  },
  del(path) {
    return this.request(path, { method: "DELETE" });
  },
};

function requireAuth() {
  if (!API.token()) window.location.href = "/login";
}

async function loadNavUser() {
  const el = document.getElementById("nav-user");
  if (!el || !API.token()) return;
  try {
    const me = await API.get("/api/auth/me");
    el.innerHTML = `${me.name} &nbsp;<button onclick="logout()" class="text-warn hover:underline">logout</button>`;
  } catch (e) {
    /* ignore */
  }
}

function logout() {
  API.clearToken();
  window.location.href = "/login";
}
