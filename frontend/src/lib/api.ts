import axios from "axios";
import type { TrendPost, TopicSummary, SentimentStats, SourceStat, DashboardAnalytics, TrendScoreEntry } from "@/types";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
});

export const fetchDashboardAnalytics = (platform?: string) =>
  api.get<DashboardAnalytics>("/v1/dashboard/analytics", { params: { platform } }).then((r) => r.data);

export const searchDashboard = (q: string, platform?: string) =>
  api.get<{ query: string; total: number; posts: TrendPost[] }>("/v1/dashboard/search", { params: { q, platform } }).then((r) => r.data);

// Legacy dashboard endpoints
export const fetchTrends = (params?: { source?: string; limit?: number }) =>
  api.get<{ posts: TrendPost[]; total: number }>("/trends/", { params }).then((r) => r.data);

export const fetchTopics = () =>
  api.get<{ topics: TopicSummary[] }>("/trends/topics").then((r) => r.data);

export const fetchSentimentStats = () =>
  api.get<SentimentStats>("/trends/stats/sentiment").then((r) => r.data);

export const fetchSourceStats = () =>
  api.get<SourceStat[]>("/trends/stats/sources").then((r) => r.data);

export const triggerFetch = (sources: string[], limit = 20) =>
  api.post("/trends/fetch", { sources, limit }).then((r) => r.data);

export const triggerAnalysis = (recompute = false) =>
  api.post("/trends/analyze", { recompute }).then((r) => r.data);

// Unified v1 endpoints
export const fetchAllTrends = (params?: { source?: string; limit?: number; sentiment?: string }) =>
  api.get<{ posts: TrendPost[]; total: number; source_breakdown: Record<string, number> }>(
    "/v1/trends/all", { params }
  ).then((r) => r.data);

export const fetchTrendStats = () =>
  api.get("/v1/trends/stats").then((r) => r.data);

// Reddit
export const fetchRedditTrends = (params?: { limit?: number; refresh?: boolean }) =>
  api.get("/v1/reddit/trends", { params }).then((r) => r.data);

export const searchReddit = (query: string, limit = 20) =>
  api.get("/v1/reddit/search", { params: { query, limit } }).then((r) => r.data);

export const fetchTwitterTrends = (params?: { limit?: number; refresh?: boolean }) =>
  api.get("/v1/twitter/trends", { params }).then((r) => r.data);

export const searchTwitter = (query: string, limit = 20) =>
  api.get("/v1/twitter/search", { params: { query, limit } }).then((r) => r.data);

// Instagram
export const fetchInstagramTrends = (params?: { limit?: number; refresh?: boolean }) =>
  api.get("/v1/instagram/trends", { params }).then((r) => r.data);

export const searchInstagram = (query: string, limit = 20) =>
  api.get("/v1/instagram/search", { params: { query, limit } }).then((r) => r.data);
