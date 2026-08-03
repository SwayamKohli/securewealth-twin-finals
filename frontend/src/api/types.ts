// src/api/types.ts
// ─────────────────────────────────────────────────────────────────────────────
// Request/response types — SecureWealth Twin Master API (Finals Architecture v2).
// These describe BACKEND shapes. Screens map these to their existing component
// props; don't edit these to match the UI.
// ─────────────────────────────────────────────────────────────────────────────

// ── Enums / unions ───────────────────────────────────────────────────────────
export type RiskProfile = 'LOW' | 'MEDIUM' | 'HIGH';
export type DeviceType = 'ANDROID' | 'IOS' | 'TABLET' | 'LAPTOP';
export type TrustStatus =
  | 'TRUSTED_DEVICE'
  | 'KNOWN_DEVICE'
  | 'NEW_DEVICE'
  | 'INACTIVE_DEVICE'
  | 'SUSPICIOUS_DEVICE'
  | 'ZERO_DAY_DEVICE';
export type AccountType = 'SAVINGS' | 'CURRENT' | 'SALARY';
export type Channel = 'UPI' | 'IMPS' | 'NEFT' | 'RTGS' | 'CARD';
export type TxnStatus = 'PENDING' | 'SUCCESS' | 'FAILED';
export type Decision = 'ALLOW' | 'WARN' | 'CHALLENGE' | 'BLOCK';
export type DepositType = 'FD' | 'RD';
export type LoanType = 'HOME' | 'CAR' | 'PERSONAL' | 'EDUCATION';
export type CardType = 'CREDIT' | 'DEBIT';
export type PhishingRiskLevel = 'SAFE' | 'LOW' | 'MEDIUM' | 'HIGH';

// ── Auth & Session ───────────────────────────────────────────────────────────
export interface RegisterRequest {
  full_name: string;
  phone: string;
  email?: string;
  date_of_birth?: string; // YYYY-MM-DD
  mpin: string;           // 6 digits
}
export interface RegisterResponse {
  message: string;
  customer_id?: string;
  user_id: string;
}

export interface LoginRequest {
  /** SecureWealth ID (CIF-style), e.g. SW10000001. Phone login removed. */
  login_id: string;
  mpin: string;
}
export interface LoginResponse {
  access_token: string;
  token_type: string; // "bearer"
}

export interface LogoutResponse {
  message: string;
}

export interface SessionResponse {
  user_id: string;
  full_name: string;
  /** Bank-issued SecureWealth ID — the login credential. */
  customer_id?: string | null;
  phone: string;
  email: string | null;
  last_login: string | null;
}

// ── User ─────────────────────────────────────────────────────────────────────
export interface UserResponse {
  user_id: string;
  full_name: string;
  phone: string;
  email: string | null;
  date_of_birth: string | null;
  risk_profile: RiskProfile;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}
export interface UpdateUserRequest {
  full_name: string;
  email?: string;
}

// ── Devices ──────────────────────────────────────────────────────────────────
export interface RegisterDeviceRequest {
  device_name: string;
  device_type: DeviceType;
  sim_id?: string;
}
export interface DeviceResponse {
  device_id: string;
  user_id: string;
  device_name: string;
  device_type: string;
  sim_id: string | null;
  trust_status: TrustStatus;
  first_seen: string;
  last_seen: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// ── Accounts ─────────────────────────────────────────────────────────────────
export interface CreateAccountRequest {
  bank_name: string;
  account_type: AccountType;
  account_number: string;
  balance: number;
  currency?: string; // default INR
}
export interface AccountResponse {
  account_id: string;
  user_id: string;
  bank_name: string;
  account_type: 'SAVINGS' | 'CURRENT' | 'SALARY';
  account_number_masked: string;
  balance: number;
  currency: string;
  created_at: string;
  updated_at: string;
}
export interface AccountBalanceResponse {
  account_id: string;
  balance: number;
  currency: string;
  last_updated: string;
}
export interface AccountSummaryResponse {
  account: AccountResponse;
  current_balance: number;
  recent_transactions: TransactionResponse[];
}

// ── Transactions ─────────────────────────────────────────────────────────────
export interface InitiateTransactionRequest {
  account_id: string;
  amount: number;
  /** Mutual fund / SIP name (investment-only workflow). */
  fund_name: string;
  /** Approved mutual-fund category, e.g. EQUITY_MUTUAL_FUND. */
  fund_category: string;
  channel: Channel;
}
export interface TransactionResponse {
  transaction_id: string;
  user_id: string;
  account_id: string;
  amount: number;
  fund_name: string;
  fund_category: string;
  channel: Channel | string;
  transaction_time: string;
  status: TxnStatus | string;
  decision: Decision | string | null;
  decision_timestamp: string | null;
  created_at: string;
  // Security verdict (populated on /initiate)
  risk_score?: number | null;
  decision_report?: string | null;
  challenge_required?: boolean | null;
  challenge_type?: string | null;
  /** Behavioural signals that actually fired, straight from the risk engine. */
  triggered_signals?: string[];
}

// ── Challenge verification (task 4.3) ──
export interface ChallengeStepResponse {
  challenge_type: string;
  trigger_signal: string;
  steps: string[];
  current_step: string | null;
  step_number: number;
  total_steps: number;
  prompt: string;
  completed: boolean;
  attempts_left: number;
  demo_otp?: string;
  verified?: boolean;
  message?: string;
  transaction_status?: 'SUCCESS' | 'FAILED';
  switched?: boolean;
  resent?: boolean;
  switched_methods?: { from: string; to: string; at: string }[];
}
export interface ChallengeMethodOption {
  method: string;
  label: string;
  description: string;
  is_current: boolean;
  available: boolean;
  unavailable_reason: string;
  /** True when picking this method adds a compensating step. */
  extra_step_required: boolean;
  replaces_with: string[];
}
export interface ChallengeMethodsResponse {
  current_step: string | null;
  switchable: boolean;
  methods: ChallengeMethodOption[];
  note: string;
}
export interface ChallengeCancelResponse {
  cancelled: boolean;
  transaction_status: string;
  reported: boolean;
  message: string;
  next_steps: string[];
}
export interface ChallengeVerifyRequest {
  answer?: string;
  acknowledged?: boolean;
}
export interface TransactionStatusResponse {
  transaction_id: string;
  status: TxnStatus;
  decision: Decision | string | null;
  decision_timestamp: string | null;
  transaction_time: string;
}
export interface GetTransactionsQuery {
  from_date?: string;
  to_date?: string;
  status?: TxnStatus;
  account_id?: string;
}

// ── Financial products ───────────────────────────────────────────────────────
export interface CreateDepositRequest {
  deposit_type: DepositType;
  principal: number;
  interest_rate: number;
  start_date: string;
  maturity_date: string;
  institution: string;
}
export interface DepositResponse {
  deposit_id: string;
  user_id: string;
  deposit_type: DepositType;
  principal: number;
  interest_rate: number;
  start_date: string;
  maturity_date: string;
  institution: string;
  created_at: string;
  updated_at: string;
}

export interface CreateLoanRequest {
  loan_type: LoanType;
  outstanding_amount: number;
  emi: number;
  interest_rate: number;
  remaining_tenure: number; // months
}
export interface LoanResponse {
  loan_id: string;
  user_id: string;
  loan_type: LoanType;
  outstanding_amount: number;
  emi: number;
  interest_rate: number;
  remaining_tenure: number;
  created_at: string;
  updated_at: string;
}

export interface CreateCardRequest {
  card_type: CardType;
  issuer: string;
  reward_type: string;
  cashback_rate: number;
  credit_limit: number;
}
export interface CardResponse {
  card_id: string;
  user_id: string;
  card_type: CardType;
  issuer: string;
  reward_type: string;
  cashback_rate: number;
  credit_limit: number;
  created_at: string;
  updated_at: string;
}

// ── Dashboard ────────────────────────────────────────────────────────────────
export interface NetWorthSummary {
  total_assets: number;
  total_liabilities: number;
  net_worth: number;
}
export interface DashboardSummaryResponse {
  user: UserResponse;
  accounts: AccountResponse[];
  net_worth: NetWorthSummary;
  recent_transactions: TransactionResponse[];
  notifications: string[];
}
export interface FinancialHealthResponse {
  total_assets: number;
  total_liabilities: number;
  net_worth: number;
  total_accounts: number;
  total_deposits: number;
  total_loans: number;
}

// ── Aggregation ──────────────────────────────────────────────────────────────
export interface LinkAccountRequest {
  bank_name: string;
  account_type: AccountType | string;
  account_number: string;
  balance: number;
  currency: string;
}
export interface AggregationSyncResponse {
  success: boolean;
  synced_accounts: number;
  message: string;
  synced_at: string;
}
export interface AggregationStatusResponse {
  accounts_connected: number;
  last_synced: string | null;
  healthy: boolean;
  status: string;
}
export interface NetWorthResponse {
  total_account_balance: number;
  total_deposits: number;
  total_assets: number;
  total_liabilities: number;
  net_worth: number;
}
export interface CashflowResponse {
  // All figures cover a rolling 30-day window, so the screens can label them
  // "this month" truthfully. They used to be lifetime totals.
  total_income: number;
  total_expenses: number;
  net_cashflow: number;
  /** Moved into mutual funds this month — counted as neither income nor spend. */
  monthly_invested?: number;
  period_days?: number;
  transaction_count: number;
}

// ── AI: Fraud ────────────────────────────────────────────────────────────────
export interface FraudEvaluateRequest {
  user_id: string;
  device_id: string;
  recipient_id: string;
  amount: number;
  hour: number;        // 0-23
  day_of_week: number; // 0-6
  otp_time_sec: number;
  session_duration: number;
  txns_last_1h: number;
  txns_last_24h: number;
}
export interface FraudEvaluateResponse {
  fraud_probability: number;
  confidence: number;
  risk_factors: unknown[];
  signal_scores: Record<string, number>;
  ml_details: Record<string, unknown>;
  baseline_used: string;
}

// ── AI: Wealth ───────────────────────────────────────────────────────────────
export interface WealthRecommendationsRequest {
  profile_data: Record<string, unknown>;
  fraud_probability?: number; // default 0.0
}
export interface WealthRecommendationsResponse {
  suppressed: boolean;
  user_id: string;
  financial_health: Record<string, unknown>;
  recommendations: unknown[];
  goal_summaries: unknown[];
  disclaimer: string;
}
export interface BuildProfileRequest {
  aa_data: Record<string, unknown>;
}
export interface BuildProfileResponse {
  profile: Record<string, unknown>;
}

// ── Security ─────────────────────────────────────────────────────────────────
export interface BehaviorSignals {
  night_owl?: boolean;
  velocity_burst?: boolean;
  amount_spike?: boolean;
  new_recipient?: boolean;
  otp_distress?: boolean;
  otp_relay?: boolean;
  round_number_anomaly?: boolean;
}
export interface EnvironmentSignals {
  ip_region?: string;
  last_login_region?: string;
  time_since_last_login_ms?: number;
  network_type?: string;
}
export interface DeviceTrustSignals {
  device_status?: string;
  device_confidence?: number;
  device_age_days?: number;
  security_signals?: string[];
}
export interface RiskEvaluateRequest {
  behavior_signals: BehaviorSignals;
  environment: EnvironmentSignals;
  device_trust: DeviceTrustSignals;
  ai_fraud_probability: number;
  ai_confidence: number;
}
export interface RiskEvaluateResponse {
  risk_score: number; // 0-100
  security_signals: Record<string, unknown>;
  timestamp: string;
  compliance_note: string;
}

export interface DecisionMakeRequest {
  transaction_id: string;
  account_id: string;
  amount: number;
  channel: string;
  risk_input: {
    behavior_signals: BehaviorSignals;
    environment: EnvironmentSignals;
    device_trust: DeviceTrustSignals;
    ai_fraud_probability: number;
    ai_confidence: number;
  };
  unknown_risk_event?: Record<string, unknown>;
}
export interface DecisionMakeResponse {
  transaction_id: string;
  account_id: string;
  amount: number;
  channel: string;
  decision: Decision | string;
  risk_score: number;
  security_signals: Record<string, unknown>;
  challenge_required: boolean;
  challenge_type: string;
  challenge_details: Record<string, unknown> | null;
  unknown_risk_applied: boolean;
  unknown_risk_decision: string;
  unknown_risk_reason_code: string;
  report: string;
  audit_note: string;
  decision_timestamp: string;
  compliance_ref: string;
}

// ── Phishing ─────────────────────────────────────────────────────────────────
export interface PhishingContext {
  transaction_hour?: number;
  amount?: number;
  is_new_recipient?: boolean;
  amount_vs_average?: number;
  recent_transaction_count?: number;
}
export interface PhishingScanRequest {
  message: string;
  context?: PhishingContext;
}
export interface PhishingScanResponse {
  phishing_score: number; // 0-1
  risk_level: PhishingRiskLevel | string;
  fired_signals: string[];
  detected_keywords: Record<string, unknown>;
  signal_groups_fired: string[];
  negative_signals_found: string[];
  signal_count: number;
  top_signal: string | null;
  message: string;
  scanned_at: string;
}
export interface BulkPhishingScanRequest {
  messages: Array<{ message: string; context?: PhishingContext }>;
}

// ── Explainability ───────────────────────────────────────────────────────────
export interface ExplainPhishingRequest {
  /** Output language: en | hi | pa (task 5.5). */
  language?: string;
  scan_result: PhishingScanResponse | Record<string, unknown>;
}
export interface ExplainPhishingResponse {
  explanation: string;
  source: string; // LLM | RULES_FALLBACK
  risk_level: string;
  score: number;
}
// ── Device Trust Explainability (was built on the backend, never called) ──
export interface ExplainDeviceTrustRequest {
  trust_result: Record<string, unknown>;
  user_profile: Record<string, unknown>;
}
export interface ExplainDeviceTrustResponse {
  device_status: string;
  device_confidence: number;
  security_signals: string[];
  customer_message: string;
  generated_by: string;
}

// ── Challenge Explainability ──
export interface ExplainChallengeRequest {
  requirement: Record<string, unknown>;
  language?: string;
  ollama_url?: string;
}
export interface ExplainChallengeResponse {
  explanation: string;
  source: string;
}

export interface ExplainDecisionRequest {
  record: Record<string, unknown>;
  ollama_url?: string;
  /** Task 5.5 — 'en' | 'hi' | 'pa'. Backend returns a localized narrative. */
  language?: string;
}
export interface ExplainDecisionResponse {
  explanation: string;
  /** 'llm' | 'template' | 'catalog' — what actually produced the text. */
  source?: string;
}
export interface ExplainRiskRequest {
  output: Record<string, unknown>;
  ollama_url?: string;
}
export interface ExplainWealthRequest {
  wealth_result: Record<string, unknown>;
  profile: Record<string, unknown>;
}
export interface WealthRecommendationExplanation {
  recommendation_id: string;
  recommendation: string;
  product: string;
  amount: number;
  tenure: string;
  /** Plain-language "why this?" — LLM-generated when available, else template. */
  explanation: string;
  expected_benefit: string;
  priority: string;
}
export interface ExplainWealthResponse {
  suppressed: boolean;
  overview: string;
  health_summary: string;
  recommendation_explanations: WealthRecommendationExplanation[];
  goal_summaries: unknown[];
  disclaimer: string;
  /** "llm" when Ollama answered, "template" otherwise — surfaced for honesty. */
  generated_by: string;
  financial_health: Record<string, unknown>;
}

// ── Health ───────────────────────────────────────────────────────────────────
export interface HealthResponse {
  status: string;
  application: string;
  version: string;
  environment: string;
  database: string;
  timestamp: string;
}
export interface ServiceHealthResponse {
  status: string;
  services: Record<string, string>;
  timestamp: string;
}

// ── Error envelope ───────────────────────────────────────────────────────────
export interface ApiErrorShape {
  detail: string;
}