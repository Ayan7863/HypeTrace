"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { TrendingUp, BarChart2, Globe, Layers, Search, X } from "lucide-react";

import Navbar from "@/components/ui/Navbar";
import StatCard from "@/components/ui/StatCard";
import TrendCard from "@/components/ui/TrendCard";
import SourceFilter from "@/components/ui/SourceFilter";
import ControlPanel from "@/components/ui/ControlPanel";
import TopicsPanel from "@/components/ui/TopicsPanel";
import AiInsightsPanel from "@/components/ui/AiInsightsPanel";
import SentimentChart from "@/components/charts/SentimentChart";
import SourceChart from "@/components/charts/SourceChart";
import TopicsChart from "@/components/charts/TopicsChart";
import TrendScoreChart from "@/components/charts/TrendScoreChart";

import { fetchDashboardAnalytics, searchDashboard } from "@/lib/api";
import type {
  TrendPost, TopicSummary, SentimentStats, SourceStat,
  TrendHistoryPoint, AiInsights,
} from "@/types";

type Source = "all" | "reddit" | "twitter" | "instagram" | "youtube" | "news";
const REFRESH_MS = 5 * 60 * 1000;

function fmt(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}k`;
  return n.toLocaleString();
}

function Skeleton({ h = "h-72" }: { h?: string }) {
  return <div className={`skeleton ${h}`} />;
}

export default function DashboardPage() {
  const [posts, setPosts] = useState<TrendPost[]>([]);
  const [topics, setTopics] = useState<TopicSummary[]>([]);
  const [sentiment, setSentiment] = useState<SentimentStats>({ positive: 0, negative: 0, neutral: 0 });
  const [sources, setSources] = useState<SourceStat[]>([]);
  const [trendHistory, setTrendHistory] = useState<TrendHistoryPoint[]>([]);
  const [aiInsights, setAiInsights] = useState<AiInsights | null>(null);
  const [activeSource, setActiveSource] = useState<Source>("all");
  const [totalPosts, setTotalPosts] = useState(0);
  const [totalEngagement, setTotalEngagement] = useState(0);
  const [topicsFound, setTopicsFound] = useState(0);
  const [topTrendScore, setTopTrendScore] = useState(0);
  const [lastUpdated, setLastUpdated] = useState<string | undefined>();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<TrendPost[] | null>(null);
  const [searching, setSearching] = useState(false);
  const searchTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [activeTopic, setActiveTopic] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const p = activeSource === "all" ? undefined : activeSource;
      const a = await fetchDashboardAnalytics(p);
      setPosts(a.top_trends ?? []);
      setTopics(a.topic_clusters ?? []);
      setSentiment(a.sentiment_distribution ?? { positive: 0, negative: 0, neutral: 0 });
      setSources(a.platform_distribution ?? []);
      setTrendHistory(a.trend_history ?? []);
      setAiInsights(a.ai_insights ?? null);
      setTotalPosts(a.total_posts ?? 0);
      setTotalEngagement(a.total_engagement ?? 0);
      setTopicsFound(a.topics_found ?? 0);
      setTopTrendScore(a.top_trend_score ?? 0);
      setLastUpdated(a.last_updated);
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? err?.message ?? "Failed to load dashboard");
    } finally {
      setLoading(false);
    }
  }, [activeSource]);

  useEffect(() => { loadData(); }, [loadData]);
  useEffect(() => {
    const id = setInterval(() => { if (!searchQuery) loadData(); }, REFRESH_MS);
    return () => clearInterval(id);
  }, [loadData, searchQuery]);

  useEffect(() => {
    if (searchTimeout.current) clearTimeout(searchTimeout.current);
    if (!searchQuery.trim()) { setSearchResults(null); return; }
    searchTimeout.current = setTimeout(async () => {
      setSearching(true);
      try {
        const p = activeSource === "all" ? undefined : activeSource;
        const res = await searchDashboard(searchQuery.trim(), p);
        setSearchResults(res.posts);
      } catch { setSearchResults([]); }
      finally { setSearching(false); }
    }, 400);
    return () => { if (searchTimeout.current) clearTimeout(searchTimeout.current); };
  }, [searchQuery, activeSource]);

  const displayedPosts = searchResults !== null
    ? searchResults
    : activeTopic
      ? posts.filter((p) => (p.topic || p.topic_label) === activeTopic)
      : posts;

  const handleTopicClick = (label: string) => {
    setActiveTopic((prev) => (prev === label ? null : label));
    setSearchQuery(""); setSearchResults(null);
  };
  const clearFilters = () => { setActiveTopic(null); setSearchQuery(""); setSearchResults(null); };

  const spikeCount = trendHistory.filter((t) => t.is_spike).length;

  return (
    <div className="min-h-screen">
      <Navbar lastUpdated={lastUpdated} />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-8 space-y-8">
        {/* Header */}
        <div className="animate-fade-in">
          <h1 className="text-2xl font-bold text-white">
            Trend Intelligence Dashboard
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Real-time AI analysis · Reddit · Twitter · YouTube · Instagram · News
          </p>
        </div>

        <ControlPanel onRefresh={loadData} />

        {error && (
          <div className="card border border-red-800/60 bg-red-950/20 text-red-400 text-sm px-4 py-3 flex items-center gap-2">
            <span className="shrink-0">⚠</span> {error}
          </div>
        )}

        {/* Stat cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard label="Total Posts" value={fmt(totalPosts)} icon={BarChart2} />
          <StatCard label="Topics Found" value={topicsFound} icon={Layers} color="text-purple-400" />
          <StatCard
            label="Total Engagement"
            value={fmt(totalEngagement)}
            icon={TrendingUp}
            color="text-emerald-400"
          />
          <StatCard
            label="Top Trend Score"
            value={topTrendScore.toFixed(1)}
            icon={Globe}
            color="text-orange-400"
            sub={spikeCount > 0 ? `⚡ ${spikeCount} viral spike${spikeCount > 1 ? "s" : ""}` : undefined}
          />
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
          <div className="xl:col-span-2">
            {loading ? <Skeleton /> : <TrendScoreChart data={trendHistory} />}
          </div>
          {loading ? <Skeleton /> : <SentimentChart data={sentiment} />}
          {loading ? <Skeleton /> : <SourceChart data={sources} />}
        </div>

        {/* Topics */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="lg:col-span-2">
            {loading ? <Skeleton h="h-80" /> : (
              <TopicsChart data={topics} onTopicClick={handleTopicClick} activeTopic={activeTopic} />
            )}
          </div>
          {loading ? <Skeleton h="h-80" /> : (
            <TopicsPanel topics={topics} onTopicClick={handleTopicClick} activeTopic={activeTopic} />
          )}
        </div>

        {/* AI Insights */}
        {loading ? <Skeleton h="h-48" /> : aiInsights && <AiInsightsPanel insights={aiInsights} />}

        {/* Posts */}
        <div>
          <div className="flex items-center justify-between mb-4 flex-wrap gap-3">
            <div className="flex items-center gap-3 flex-wrap">
              <h2 className="text-base font-semibold text-white">Trending Posts</h2>
              {activeTopic && (
                <span className="flex items-center gap-1 text-xs bg-brand-500/15 text-brand-500 border border-brand-500/20 px-2.5 py-1 rounded-full">
                  {activeTopic}
                  <button onClick={clearFilters} className="ml-1 hover:text-white transition-colors"><X size={10} /></button>
                </span>
              )}
            </div>
            <div className="flex items-center gap-3 flex-wrap">
              <div className="relative">
                <Search size={12} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => { setSearchQuery(e.target.value); setActiveTopic(null); }}
                  placeholder="Search posts…"
                  className="bg-gray-800 border border-gray-700 text-sm text-white placeholder-gray-500 rounded-full pl-8 pr-8 py-1.5 w-44 focus:outline-none focus:ring-1 focus:ring-brand-500 focus:border-brand-500/50 transition-all"
                />
                {searchQuery && (
                  <button onClick={clearFilters} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-white transition-colors">
                    <X size={11} />
                  </button>
                )}
              </div>
              <SourceFilter active={activeSource} onChange={(s) => { setActiveSource(s as Source); clearFilters(); }} />
            </div>
          </div>

          {loading ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {Array.from({ length: 6 }).map((_, i) => <div key={i} className="skeleton h-44" />)}
            </div>
          ) : searching ? (
            <div className="card text-center py-10 text-gray-500 text-sm">Searching…</div>
          ) : displayedPosts.length === 0 ? (
            <div className="card text-center py-16 text-gray-500">
              {searchQuery
                ? <p>No results for &quot;{searchQuery}&quot;</p>
                : <><p className="text-lg font-medium">No posts yet</p><p className="text-sm mt-1">Click &quot;Fetch Trends&quot; to pull live data</p></>
              }
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {displayedPosts.map((post) => (
                <TrendCard key={post.post_id ?? post.id ?? post._id} post={post} />
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
