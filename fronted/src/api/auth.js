import http from "./http";

export async function register(payload) {
  const response = await http.post("/auth/register", payload);
  return response.data;
}

export async function login(payload) {
  const response = await http.post("/auth/login", payload);
  return response.data;
}

export async function loginByEmailCode(payload) {
  const response = await http.post("/auth/login/email", payload);
  return response.data;
}

export async function sendEmailCode(payload) {
  const response = await http.post("/auth/email-code", payload);
  return response.data;
}

export async function getCurrentUser() {
  const response = await http.get("/auth/me");
  return response.data;
}

export async function updateCurrentUserSignature(payload) {
  const response = await http.put("/auth/me/signature", payload);
  return response.data;
}
