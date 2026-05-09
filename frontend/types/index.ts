export type FreshnessTier = "STREAMING" | "NEAR_REALTIME" | "POLLED" | "FILING_DELAYED";

export type SignalLabel = "STRONG_WATCH" | "WATCH" | "NEUTRAL" | "AVOID";

export interface SignalScore {
  id: number;
  symbol: string;
  scored_at: string;
  news_sentiment_score: number;
  catalyst_score: number;
  analyst_momentum_score: number;
  insider_signal_score: number;
  price_confirmation_score: number;
  total_trade_score: number;
  label: SignalLabel;
  explanation?: ExplanationItem[];
}

export interface ExplanationItem {
  type: "bullish" | "bearish" | "neutral" | "mild_bullish" | "mild_bearish";
  text: string;
}

export interface NewsEvent {
  id: number;
  symbol: string;
  headline: string;
  summary?: string;
  url?: string;
  sentiment_score: number;
  freshness_tier: FreshnessTier;
  event_timestamp: string;
  source_name: string;
}

export interface AnalystEvent {
  id: number;
  symbol: string;
  analyst_firm: string;
  analyst_name?: string;
  action: string;
  from_rating?: string;
  to_rating?: string;
  from_target?: number;
  to_target?: number;
  momentum_score?: number;
  freshness_tier: FreshnessTier;
  event_timestamp: string;
  source_name: string;
}

export interface InsiderEvent {
  id: number;
  symbol: string;
  insider_name: string;
  insider_title?: string;
  transaction_type: string;
  shares?: number;
  price_per_share?: number;
  total_value?: number;
  signal_score?: number;
  freshness_tier: FreshnessTier;
  event_timestamp: string;
  filing_date?: string;
  transaction_date?: string;
  source_name: string;
}

export interface Ticker {
  symbol: string;
  name?: string;
  sector?: string;
  industry?: string;
  exchange?: string;
  market_cap?: number;
}

export interface ProviderHealth {
  id: number;
  provider_name: string;
  freshness_tier?: FreshnessTier;
  is_enabled: boolean;
  poll_interval_s: number;
  last_sync_at?: string;
  last_event_at?: string;
  error_count: number;
  last_error?: string;
  status: "healthy" | "degraded" | "down" | "unknown";
}

export type WsMessage =
  | { v: 1; type: "news"; symbol: string; freshness_tier: FreshnessTier; headline: string; sentiment_score: number; event_timestamp: string; source: string }
  | { v: 1; type: "analyst"; symbol: string; freshness_tier: FreshnessTier; action: string; firm: string; to_rating: string; to_target?: number; momentum_score: number; event_timestamp: string }
  | { v: 1; type: "insider"; symbol: string; freshness_tier: FreshnessTier; insider_name: string; transaction_type: string; shares?: number; total_value?: number; signal_score?: number; event_timestamp: string; freshness_note?: string }
  | { v: 1; type: "score"; symbol: string; total_trade_score: number; label: SignalLabel; scored_at: string }
  | { v: 1; type: "heartbeat"; ts: number };
