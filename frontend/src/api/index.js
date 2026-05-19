import { api } from "./client";

export const uploadApi = {
  history: () => api.get("/upload/history").then((r) => r.data),
  greythr: (file, period_start, period_end) => {
    const fd = new FormData();
    fd.append("file", file);
    fd.append("period_start", period_start);
    fd.append("period_end", period_end);
    return api
      .post("/upload/greythr", fd, { headers: { "Content-Type": "multipart/form-data" } })
      .then((r) => r.data);
  },
  biometric: (file, period_start, period_end) => {
    const fd = new FormData();
    fd.append("file", file);
    fd.append("period_start", period_start);
    fd.append("period_end", period_end);
    return api
      .post("/upload/biometric", fd, { headers: { "Content-Type": "multipart/form-data" } })
      .then((r) => r.data);
  },
  roster: (file) => {
    const fd = new FormData();
    fd.append("file", file);
    return api
      .post("/upload/roster", fd, { headers: { "Content-Type": "multipart/form-data" } })
      .then((r) => r.data);
  },
  delete: (uploadId) => api.delete(`/upload/${uploadId}`),
};

export const pipelineApi = {
  run: (period_start, period_end) =>
    api.post("/pipeline/run", { period_start, period_end }).then((r) => r.data),
  status: (period_start, period_end) =>
    api.get(`/pipeline/status/${period_start}/${period_end}`).then((r) => r.data),
};

export const employeesApi = {
  list: () => api.get("/employees").then((r) => r.data),
  get: (empCode) => api.get(`/employees/${empCode}`).then((r) => r.data),
  updateEmail: (empCode, email) =>
    api.patch(`/employees/${empCode}/email`, { email }).then((r) => r.data),
};

export const attendanceApi = {
  summary: (period_start, period_end) =>
    api.get("/attendance", { params: { period_start, period_end } }).then((r) => r.data),
  forEmployee: (empCode, period_start, period_end) =>
    api
      .get(`/attendance/${empCode}`, { params: { period_start, period_end } })
      .then((r) => r.data),
};

export const leaveApi = {
  summary: (period_start, period_end) =>
    api.get("/leave", { params: { period_start, period_end } }).then((r) => r.data),
  forEmployee: (empCode, period_start, period_end) =>
    api.get(`/leave/${empCode}`, { params: { period_start, period_end } }).then((r) => r.data),
};

export const flagsApi = {
  list: (params) => api.get("/flags", { params }).then((r) => r.data),
  resolve: (flagId) => api.patch(`/flags/${flagId}/resolve`).then((r) => r.data),
  recompute: (period_start, period_end) =>
    api.post("/flags/recompute", { period_start, period_end }).then((r) => r.data),
};

export const emailApi = {
  configStatus: () => api.get("/email/config-status").then((r) => r.data),
  templates: (includeInactive = false) =>
    api
      .get("/email/templates", { params: { include_inactive: includeInactive } })
      .then((r) => r.data),
  createTemplate: (payload) => api.post("/email/templates", payload).then((r) => r.data),
  updateTemplate: (id, payload) =>
    api.put(`/email/templates/${id}`, payload).then((r) => r.data),
  deleteTemplate: (id) => api.delete(`/email/templates/${id}`),
  send: (flag_ids, template_id, preview_only = false) =>
    api.post("/email/send", { flag_ids, template_id, preview_only }).then((r) => r.data),
  logs: (params) => api.get("/email/logs", { params }).then((r) => r.data),
};

export const settingsApi = {
  thresholds: () => api.get("/settings/thresholds").then((r) => r.data),
  updateThreshold: (flagType, value) =>
    api
      .put(`/settings/thresholds/${flagType}`, { threshold_value: value })
      .then((r) => r.data),
};

export const analyticsApi = {
  overview: (period_start, period_end) =>
    api.get("/analytics/overview", { params: { period_start, period_end } }).then((r) => r.data),
  attendanceChart: (period_start, period_end) =>
    api
      .get("/analytics/attendance-chart", { params: { period_start, period_end } })
      .then((r) => r.data),
  flagDistribution: (period_start, period_end) =>
    api
      .get("/analytics/flag-distribution", { params: { period_start, period_end } })
      .then((r) => r.data),
  lateTrend: () => api.get("/analytics/late-trend").then((r) => r.data),
};
