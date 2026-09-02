import http, { API_BASE_URL, handleUnauthorized } from "./http";
import { getToken } from "../utils/auth";

export async function listNotebooks() {
  const response = await http.get("/notebooks");
  return response.data;
}

export async function createNotebook(payload) {
  const response = await http.post("/notebooks", payload);
  return response.data;
}

export async function deleteNotebook(notebookId) {
  const response = await http.delete(`/notebooks/${notebookId}`);
  return response.data;
}

export async function getNotebookWorkspace(notebookId) {
  const response = await http.get(`/notebooks/${notebookId}`);
  return response.data;
}

export async function uploadNotebookAttachment(notebookId, file) {
  const formData = new FormData();
  formData.append("file", file);
  const response = await http.post(`/notebooks/${notebookId}/attachments`, formData);
  return response.data;
}

export async function uploadNotebookSource(notebookId, file, onUploadProgress) {
  const formData = new FormData();
  formData.append("file", file);
  const response = await http.post(`/notebooks/${notebookId}/sources`, formData, {
    onUploadProgress,
    timeout: 300000,
  });
  return response.data;
}

export async function deleteNotebookSource(notebookId, sourceId) {
  const response = await http.delete(`/notebooks/${notebookId}/sources/${sourceId}`);
  return response.data;
}

export async function deleteNotebookAttachment(notebookId, attachmentId) {
  const response = await http.delete(`/notebooks/${notebookId}/attachments/${attachmentId}`);
  return response.data;
}

export async function streamNotebookChat(notebookId, payload, onEvent) {
  const response = await fetch(`${API_BASE_URL}/notebooks/${notebookId}/chat`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${getToken()}`,
      Accept: "text/event-stream",
      "Cache-Control": "no-cache",
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    handleUnauthorized(response.status);
    const data = await response.json().catch(() => null);
    const error = new Error(data?.detail?.message || "对话请求失败");
    error.response = {
      status: response.status,
      data,
    };
    throw error;
  }
  if (!response.body) {
    throw new Error("当前浏览器无法读取流式回复");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";
  let eventError = null;

  const dispatchEvent = (event) => {
    try {
      const result = onEvent(event);

      if (result && typeof result.catch === "function") {
        result.catch((error) => {
          eventError = error;
          reader.cancel().catch(() => {});
        });
      }
    } catch (error) {
      eventError = error;
      throw error;
    }
  };

  while (true) {
    const { done, value } = await reader.read();
    buffer += decoder.decode(value || new Uint8Array(), { stream: !done });
    let boundary = buffer.indexOf("\n\n");

    while (boundary !== -1) {
      const block = buffer.slice(0, boundary);
      buffer = buffer.slice(boundary + 2);
      const data = block
        .split("\n")
        .filter((line) => line.startsWith("data: "))
        .map((line) => line.slice(6))
        .join("\n");

      if (data) {
        dispatchEvent(JSON.parse(data));
      }
      if (eventError) {
        throw eventError;
      }
      boundary = buffer.indexOf("\n\n");
    }

    if (done) {
      break;
    }
  }

  if (eventError) {
    throw eventError;
  }
}

export async function generateStudioArtifact(notebookId, payload) {
  const response = await http.post(`/notebooks/${notebookId}/artifacts`, payload);
  return response.data;
}

export async function deleteStudioArtifact(notebookId, artifactId) {
  const response = await http.delete(`/notebooks/${notebookId}/artifacts/${artifactId}`);
  return response.data;
}

export async function submitQuizAttempt(notebookId, artifactId, payload) {
  const response = await http.post(
    `/notebooks/${notebookId}/artifacts/${artifactId}/quiz-attempt`,
    payload,
  );
  return response.data;
}

export async function createNotebookNote(notebookId, payload) {
  const response = await http.post(`/notebooks/${notebookId}/notes`, payload);
  return response.data;
}

export async function saveMessageAsNote(notebookId, messageId) {
  const response = await http.post(`/notebooks/${notebookId}/notes/from-message`, {
    message_id: messageId,
  });
  return response.data;
}

export async function deleteNotebookNote(notebookId, noteId) {
  const response = await http.delete(`/notebooks/${notebookId}/notes/${noteId}`);
  return response.data;
}
