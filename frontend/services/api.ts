import axios from "axios";

const API_URL = "http://localhost:8000";

const HARDCODED_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkZW1vIiwiZXhwIjoxNzc4MzgyNTYwfQ.ofzqI-avk2nYxRwj3cR6Ei_Xy9iyQTWJ_Eal4bBFVgs";

export const api = axios.create({
  baseURL: API_URL,
  timeout: 10_000,
  headers: {
    Authorization: `Bearer ${HARDCODED_TOKEN}`,
  },
});

export function logout() {}
export async function login(u: string, p: string) {}
export const fetchScores = () => api.get("/api/scores/").then((r) => r.data);
export const fetchNews = (symbol?: string, hours = 24) =>
  api.get("/api/events/news", { params: { symbol, hours, limit: 50 } }).then((r) => r.data);
export const fetchAnalyst = (symbol?: string) =>
  api.get("/api/events/analyst", { params: { symbol, hours: 72 } }).then((r) => r.data);
export const fetchInsider = (symbol?: string) =>
  api.get("/api/events/insider", { params: { symbol, hours: 168 } }).then((r) => r.data);
export const fetchTickers = () => api.get("/api/tickers/").then((r) => r.data);
export const fetchProviders = () => api.get("/api/providers/").then((r) => r.data);
export const fetchTicker = (symbol: string) => api.get(`/api/tickers/${symbol}`).then((r) => r.data);
export const fetchScoreForSymbol = (symbol: string) => api.get(`/api/scores/${symbol}`).then((r) => r.data);
