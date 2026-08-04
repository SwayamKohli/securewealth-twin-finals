// src/api/apiService.ts
// ─────────────────────────────────────────────────────────────────────────────
// THE ONE FILE every screen imports for backend access.
// SecureWealth Twin Master API — Finals Architecture v2.
//
// Usage in a screen:
//   import { api, ApiError } from '../api/apiService';
//   const dash = await api.getDashboard();
// ─────────────────────────────────────────────────────────────────────────────

import { API_BASE_URL, API_HOST, REQUEST_TIMEOUT_MS, LONG_TIMEOUT_MS } from './config';
import { getCachedToken, loadToken, saveToken, clearToken } from './authStorage';
import type {
  RegisterRequest, RegisterResponse,
  LoginRequest, LoginResponse, LogoutResponse, SessionResponse,
  UserResponse, UpdateUserRequest,
  RegisterDeviceRequest, DeviceResponse,
  CreateAccountRequest, AccountResponse, AccountBalanceResponse, AccountSummaryResponse,
  InitiateTransactionRequest, TransactionResponse, TransactionStatusResponse, GetTransactionsQuery,
  CreateDepositRequest, DepositResponse,
  CreateLoanRequest, LoanResponse,
  CreateCardRequest, CardResponse,
  DashboardSummaryResponse, FinancialHealthResponse,
  LinkAccountRequest, AggregationSyncResponse, AggregationStatusResponse,
  NetWorthResponse, CashflowResponse,
  FraudEvaluateRequest, FraudEvaluateResponse,
  WealthRecommendationsRequest, WealthRecommendationsResponse,
  BuildProfileRequest, BuildProfileResponse,
  RiskEvaluateRequest, RiskEvaluateResponse,
  DecisionMakeRequest, DecisionMakeResponse,
  PhishingScanRequest, PhishingScanResponse, BulkPhishingScanRequest,
  ExplainPhishingRequest, ExplainPhishingResponse,
  ExplainDecisionRequest, ExplainDecisionResponse,
  ExplainRiskRequest, ExplainWealthRequest,
  HealthResponse, ServiceHealthResponse,
} from './types';

// ── Error type ───────────────────────────────────────────────────────────────
/** Sentinel status for "request sent, no reply in time" (see request()). */
export const TIMEOUT_STATUS = -1;

export class ApiError extends Error {
  status: number;
  detail?: unknown;
  constructor(status: number, message: string, detail?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
  }
  get isAuthError() {
    return this.status === 401 || this.status === 403;
  }
  /** Server was never reached — safe to assume nothing happened. */
  get isNetworkError() {
    return this.status === 0;
  }
  /**
   * Request was sent but no reply arrived in time. The server MAY have done
   * the work. Never tell the customer the action failed on this.
   */
  get isTimeout() {
    return this.status === TIMEOUT_STATUS;
  }
  /** Either failure mode, for screens that only need "no data". */
  get isConnectivityError() {
    return this.status === 0 || this.status === TIMEOUT_STATUS;
  }
}

// ── Core request helper ──────────────────────────────────────────────────────
type Query = Record<string, string | number | boolean | undefined | null>;

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE';
  body?: unknown;
  query?: Query;
  auth?: boolean;   // attach JWT (default true)
  raw?: boolean;    // use API_HOST (no /api/v1) — for /dashboard/* endpoints
  /**
   * Override the default timeout. Needed for /transactions/initiate: the first
   * one after the server starts loads the fraud model, which can push the call
   * past 20s. Timing out there told the customer the investment failed while
   * the backend had already completed it — the worst possible wrong answer.
   */
  timeoutMs?: number;
}

function buildUrl(path: string, query?: Query, raw?: boolean): string {
  const base = raw ? API_HOST : API_BASE_URL;
  let url = `${base}${path}`;
  if (query) {
    const params = Object.entries(query)
      .filter(([, v]) => v !== undefined && v !== null && v !== '')
      .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(String(v))}`);
    if (params.length) url += `?${params.join('&')}`;
  }
  return url;
}

async function request<T>(path: string, opts: RequestOptions = {}): Promise<T> {
  const { method = 'GET', body, query, auth = true, raw = false, timeoutMs } = opts;

  const headers: Record<string, string> = { Accept: 'application/json' };
  if (body !== undefined) headers['Content-Type'] = 'application/json';

  if (auth) {
    let token = getCachedToken();
    if (!token) token = await loadToken();
    if (token) headers.Authorization = `Bearer ${token}`;
  }

  const controller = new AbortController();
  const timeout = setTimeout(
    () => controller.abort(),
    timeoutMs ?? REQUEST_TIMEOUT_MS
  );

  let res: Response;
  try {
    res = await fetch(buildUrl(path, query, raw), {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    });
  } catch (e: any) {
    clearTimeout(timeout);
    // A TIMEOUT and an UNREACHABLE server are very different situations. On a
    // timeout the server may well have completed the work, so callers that
    // change money must not tell the customer it failed. ApiError.status
    // distinguishes them: 0 = never reached, -1 = sent but no answer in time.
    const aborted = e?.name === 'AbortError';
    throw new ApiError(
      aborted ? TIMEOUT_STATUS : 0,
      aborted
        ? 'The server is taking longer than usual to answer.'
        : 'Cannot reach the server. Check your connection.',
      e
    );
  }
  clearTimeout(timeout);

  const text = await res.text();
  let data: any = undefined;
  if (text) {
    try { data = JSON.parse(text); } catch { data = text; }
  }

  if (!res.ok) {
    // API standard error shape is { detail: "..." }
    const message =
      (data && (data.detail || data.message || data.error)) ||
      `Request failed (${res.status})`;
    throw new ApiError(res.status, String(message), data);
  }

  return data as T;
}

// ─────────────────────────────────────────────────────────────────────────────
// Public API surface
// ─────────────────────────────────────────────────────────────────────────────
export const api = {
  // ── token helpers ──
  saveToken,
  clearToken,
  loadToken,

  // ── Auth & Session ──
  register: (b: RegisterRequest) =>
    request<RegisterResponse>('/api/v1/auth/register', { method: 'POST', body: b, auth: false }),

  /** Logs in AND persists the JWT. */
  async login(b: LoginRequest): Promise<LoginResponse> {
    const res = await request<LoginResponse>('/api/v1/auth/login', {
      method: 'POST', body: b, auth: false,
    });
    if (res?.access_token) await saveToken(res.access_token);
    return res;
  },

  /** Calls server logout then clears the local token (always clears locally). */
  async logout(): Promise<void> {
    try {
      await request<LogoutResponse>('/api/v1/auth/logout', { method: 'POST' });
    } catch {
      // Ignore server errors — client-side logout must still succeed.
    } finally {
      await clearToken();
    }
  },

  getSession: () =>
    request<SessionResponse>('/api/v1/auth/session'),

  // ── User ──
  getCurrentUser: () =>
    request<UserResponse>('/api/v1/users/me'),
  updateUser: (b: UpdateUserRequest) =>
    request<UserResponse>('/api/v1/users/me', { method: 'PUT', body: b }),
  deactivateUser: () =>
    request<{ message: string }>('/api/v1/users/me', { method: 'DELETE' }),

  // ── Devices ──
  registerDevice: (b: RegisterDeviceRequest) =>
    request<DeviceResponse>('/api/v1/devices/register', { method: 'POST', body: b }),
  getDevices: () =>
    request<DeviceResponse[]>('/api/v1/devices'),
  getCurrentDevice: () =>
    request<DeviceResponse>('/api/v1/devices/current'),
  deactivateDevice: (deviceId: string) =>
    request<{ message: string }>(`/api/v1/devices/${deviceId}`, { method: 'DELETE' }),

  // ── Accounts ──
  createAccount: (b: CreateAccountRequest) =>
    request<AccountResponse>('/api/v1/accounts/', { method: 'POST', body: b }),
  getAccounts: () =>
    request<AccountResponse[]>('/api/v1/accounts/'),
  getAccount: (accountId: string) =>
    request<AccountResponse>(`/api/v1/accounts/${accountId}`),
  getAccountBalance: (accountId: string) =>
    request<AccountBalanceResponse>(`/api/v1/accounts/${accountId}/balance`),
  getAccountSummary: (accountId: string) =>
    request<AccountSummaryResponse>(`/api/v1/accounts/${accountId}/summary`),

  // ── Transactions ──
  initiateTransaction: (b: InitiateTransactionRequest) =>
    // The full security pipeline plus an audit write. Never cut this short:
    // a timeout here is indistinguishable from a failure to the customer.
    request<TransactionResponse>('/api/v1/transactions/initiate', {
      method: 'POST',
      body: b,
      timeoutMs: LONG_TIMEOUT_MS,
    }),
  getTransactions: (q?: GetTransactionsQuery) =>
    request<TransactionResponse[]>('/api/v1/transactions/', { query: q as Query }),
  getTransaction: (transactionId: string) =>
    request<TransactionResponse>(`/api/v1/transactions/${transactionId}`),
  getTransactionStatus: (transactionId: string) =>
    request<TransactionStatusResponse>(`/api/v1/transactions/${transactionId}/status`),

  // ── Financial products ──
  createDeposit: (b: CreateDepositRequest) =>
    request<DepositResponse>('/api/v1/deposits/', { method: 'POST', body: b }),
  getDeposits: () =>
    request<DepositResponse[]>('/api/v1/deposits/'),
  getDeposit: (id: string) =>
    request<DepositResponse>(`/api/v1/deposits/${id}`),
  deleteDeposit: (id: string) =>
    request<{ message: string }>(`/api/v1/deposits/${id}`, { method: 'DELETE' }),

  createLoan: (b: CreateLoanRequest) =>
    request<LoanResponse>('/api/v1/loans/', { method: 'POST', body: b }),
  getLoans: () =>
    request<LoanResponse[]>('/api/v1/loans/'),
  getLoan: (id: string) =>
    request<LoanResponse>(`/api/v1/loans/${id}`),
  deleteLoan: (id: string) =>
    request<{ message: string }>(`/api/v1/loans/${id}`, { method: 'DELETE' }),

  createCard: (b: CreateCardRequest) =>
    request<CardResponse>('/api/v1/cards/', { method: 'POST', body: b }),
  getCards: () =>
    request<CardResponse[]>('/api/v1/cards/'),
  getCard: (id: string) =>
    request<CardResponse>(`/api/v1/cards/${id}`),
  deleteCard: (id: string) =>
    request<{ message: string }>(`/api/v1/cards/${id}`, { method: 'DELETE' }),

  // ── Dashboard (NOTE: not under /api/v1 → raw:true) ──
  getDashboard: () =>
    request<DashboardSummaryResponse>('/dashboard/', { raw: true }),
  getActivity: () =>
    request<TransactionResponse[]>('/dashboard/activity', { raw: true }),
  getFinancialHealth: () =>
    request<FinancialHealthResponse>('/dashboard/health', { raw: true }),

  // ── Consent (task 2.1) ──
  getConsent: () =>
    request<{ aa_consent: boolean; aa_consent_at: string | null; message: string }>(
      '/api/v1/aggregation/consent'),
  grantConsent: () =>
    request<{ aa_consent: boolean; aa_consent_at: string | null; message: string }>(
      '/api/v1/aggregation/consent', { method: 'POST' }),
  revokeConsent: () =>
    request<{ aa_consent: boolean; aa_consent_at: string | null; message: string }>(
      '/api/v1/aggregation/consent', { method: 'DELETE' }),

  // ── Aggregation ──
  getAggregatedAccounts: () =>
    request<AccountResponse[]>('/api/v1/aggregation/accounts'),
  linkAccount: (b: LinkAccountRequest) =>
    request<AccountResponse>('/api/v1/aggregation/accounts/link', { method: 'POST', body: b }),
  syncAggregation: (force_refresh = false) =>
    request<AggregationSyncResponse>('/api/v1/aggregation/sync', {
      method: 'POST',
      body: { force_refresh },
    }),
  getAggregationStatus: () =>
    request<AggregationStatusResponse>('/api/v1/aggregation/status'),
  getNetWorth: () =>
    request<NetWorthResponse>('/api/v1/aggregation/net-worth'),
  getCashflow: () =>
    request<CashflowResponse>('/api/v1/aggregation/cashflow'),

  // ── AI ──
  evaluateFraud: (b: FraudEvaluateRequest) =>
    request<FraudEvaluateResponse>('/api/v1/ai/fraud/evaluate', {
      method: 'POST', body: b, timeoutMs: LONG_TIMEOUT_MS }),
  getWealthRecommendations: (b: WealthRecommendationsRequest) =>
    request<WealthRecommendationsResponse>('/api/v1/ai/wealth/recommendations', {
      method: 'POST', body: b, timeoutMs: LONG_TIMEOUT_MS }),
  buildProfile: (b: BuildProfileRequest) =>
    request<BuildProfileResponse>('/api/v1/ai/profile/build', { method: 'POST', body: b }),

  // ── Security ──
  evaluateRisk: (b: RiskEvaluateRequest) =>
    request<RiskEvaluateResponse>('/api/v1/security/risk/evaluate', { method: 'POST', body: b }),
  makeDecision: (b: DecisionMakeRequest) =>
    request<DecisionMakeResponse>('/api/v1/security/decision/make', { method: 'POST', body: b }),

  /** The customer's own security history (sourced from the audit chain). */
  getMySecurityActivity: () =>
    request<{ count: number; activities: any[] }>('/api/v1/security/my-activity'),

  // ── Challenge verification (task 4.3) ──
  startChallenge: (transactionId: string) =>
    request<import('./types').ChallengeStepResponse>(
      `/api/v1/security/challenge/${transactionId}/start`,
      { method: 'POST', timeoutMs: LONG_TIMEOUT_MS }),
  // The final verify completes the investment end to end — the slowest call in
  // the app. A timeout here previously stranded the customer on the OTP screen
  // while the money had already been invested.
  verifyChallenge: (transactionId: string, b: import('./types').ChallengeVerifyRequest) =>
    request<import('./types').ChallengeStepResponse>(
      `/api/v1/security/challenge/${transactionId}/verify`,
      { method: 'POST', body: b, timeoutMs: LONG_TIMEOUT_MS }),

  /** Task 4.3b — alternative verification methods for the current step. */
  getChallengeMethods: (transactionId: string) =>
    request<import('./types').ChallengeMethodsResponse>(
      `/api/v1/security/challenge/${transactionId}/methods`),
  switchChallengeMethod: (transactionId: string, method: string) =>
    request<import('./types').ChallengeStepResponse>(
      `/api/v1/security/challenge/${transactionId}/method`,
      { method: 'POST', body: { method }, timeoutMs: LONG_TIMEOUT_MS }),
  resendChallengeOtp: (transactionId: string) =>
    request<import('./types').ChallengeStepResponse>(
      `/api/v1/security/challenge/${transactionId}/resend-otp`, { method: 'POST' }),
  /** Task 4.3c — "this wasn't me": drops the held investment and reports it. */
  cancelChallenge: (transactionId: string, reason?: string) =>
    request<import('./types').ChallengeCancelResponse>(
      `/api/v1/security/challenge/${transactionId}/cancel`,
      { method: 'POST', body: { reason }, timeoutMs: LONG_TIMEOUT_MS }),

  // ── Phishing ──
  scanPhishing: (b: PhishingScanRequest) =>
    request<PhishingScanResponse>('/api/v1/phishing/scan', { method: 'POST', body: b }),
  bulkScanPhishing: (b: BulkPhishingScanRequest) =>
    // Backend expects a bare array of {message, context} objects.
    request<PhishingScanResponse[]>('/api/v1/phishing/bulk-scan', {
      method: 'POST',
      body: b.messages,
    }),

  // ── Explainability ──
  explainPhishing: (b: ExplainPhishingRequest) =>
    request<ExplainPhishingResponse>('/api/v1/ai/explainability/phishing', { method: 'POST', body: b , timeoutMs: LONG_TIMEOUT_MS }),
  /** Task 4.4 — plain-language device trust status for the Profile screen. */
  explainDeviceTrust: (b: import('./types').ExplainDeviceTrustRequest) =>
    request<import('./types').ExplainDeviceTrustResponse>(
      '/api/v1/ai/explainability/device-trust', { method: 'POST', body: b , timeoutMs: LONG_TIMEOUT_MS }),
  /** Task 4.3 — why this verification step is being asked for. */
  explainChallenge: (b: import('./types').ExplainChallengeRequest) =>
    request<import('./types').ExplainChallengeResponse>(
      '/api/v1/ai/explainability/challenge', { method: 'POST', body: b , timeoutMs: LONG_TIMEOUT_MS }),
  explainDecision: (b: ExplainDecisionRequest) =>
    request<ExplainDecisionResponse>('/api/v1/ai/explainability/decision', { method: 'POST', body: b , timeoutMs: LONG_TIMEOUT_MS }),
  explainRisk: (b: ExplainRiskRequest) =>
    request<{ explanation: string }>('/api/v1/ai/explainability/risk', { method: 'POST', body: b , timeoutMs: LONG_TIMEOUT_MS }),
  explainWealth: (b: ExplainWealthRequest) =>
    request<import('./types').ExplainWealthResponse>(
      '/api/v1/ai/explainability/wealth', { method: 'POST', body: b , timeoutMs: LONG_TIMEOUT_MS }),

  // ── Health ──
  health: () =>
    request<HealthResponse>('/api/v1/health/', { auth: false }),
  serviceHealth: () =>
    request<ServiceHealthResponse>('/api/v1/health/services', { auth: false }),
};

export type Api = typeof api;