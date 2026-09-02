import http from "./http";

export async function listForumPosts(params = {}) {
  const response = await http.get("/forum/posts", {
    params,
  });
  return response.data;
}

export async function createForumPost(payload) {
  const response = await http.post("/forum/posts", payload);
  return response.data;
}

export async function getForumPost(postId) {
  const response = await http.get(`/forum/posts/${postId}`);
  return response.data;
}

export async function deleteForumPost(postId) {
  const response = await http.delete(`/forum/posts/${postId}`);
  return response.data;
}

export async function createForumComment(postId, payload) {
  const response = await http.post(`/forum/posts/${postId}/comments`, payload);
  return response.data;
}

export async function toggleForumPostLike(postId) {
  const response = await http.post(`/forum/posts/${postId}/like`);
  return response.data;
}
