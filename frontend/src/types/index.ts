export interface TrendPost {
  _id: string;
  id?: string;
  platform: "reddit" | "twitter" | "youtube" | "instagram" | "news";
  title: string;
  text?: string;
  content: string;
  author: string;
  url: string;
  engagement: { likes: number; comments: number; shares: number };
  timestamp: string;
  sentiment_score: number | null;
  sentiment_label: "positive" | "negative" | "neutral" | null;
  topic: string | null;
  embedding_vector: number[] | null;
  trend_score: number | null;
  is_spike?: boolean;
  trend_phase?: "Viral" | "Emerging" | "Declining" | "Stable";
  virality_score?: number;
  hours_old?: number;
  ai_summary?: string;
  // Legacy
  source?: "reddit" | "twitter" | "youtube" | "instagram" | "news";
  post_id?: string;
  score?: number;
  sentiment?: "positive" | "negative" | "neutral" | null;
  topic_label?: string | null;
  topic_cluster?: number | null;
  fetched_at?: string;
}

export interface TopicSummary {
  topic_label: string;
  post_count: number;
  avg_sentiment: number;
  avg_trend_score: number;
  avg_virality?: number;
  top_sources: string[];
  spike_count?: number;
  percentage?: number;
  dominant_phase?: string;
  summary?: string;
}

export interface SentimentStats {
  positive: number;
  negative: number;
  neutral: number;
  positive_pct?: number;
  negative_pct?: number;
  neutral_pct?: number;
}

export interface SourceStat {
  source: string;
  count: number;
  avg_trend_score: number;
  trend_score?: number;
  percentage?: number;
  total_engagement?: number;
}

export interface TrendScoreEntry {
  title: string;
  score: number;
  platform: string;
  is_spike?: boolean;
  sentiment?: string;
  engagement?: number;
  trend_phase?: string;
  virality_score?: number;
}

export interface TrendHistoryPoint {
  index: number;
  label: string;
  score: number;
  peak: number;
  momentum: number;
  decay_curve: number[];
  is_spike: boolean;
  platform: string;
  title: string;
  sentiment: string;
  engagement: number;
  trend_phase: string;
  virality_score: number;
  timestamp: string;
}

export interface AiInsights {
  summary: string;
  opportunities: string[];
  pain_points: string[];
  recommendations: string[];
  market_predictions: string[];
  dominant_sentiment: string;
  top_topics: string[];
  spike_count: number;
  avg_trend_score: number;
}

export interface DashboardAnalytics {
  total_posts: number;
  total_engagement: number;
  topics_found: number;
  top_trend_score: number;
  sentiment_distribution: SentimentStats;
  platform_distribution: SourceStat[];
  top_trends: TrendPost[];
  topic_clusters: TopicSummary[];
  trend_scores: TrendScoreEntry[];
  trend_history: TrendHistoryPoint[];
  ai_insights: AiInsights;
  last_updated: string;
}
