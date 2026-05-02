export interface TelegramUser {
  id: number
  first_name: string
  last_name?: string
  username?: string
  language_code?: string
  photo_url?: string
}

export interface ActiveSubscription {
  subscription_id: number
  start_date: string
  end_date: string
  duration_months: number
  is_active: boolean
  auto_renew_enabled: boolean
  days_remaining: number
  traffic_limit_gb: number | null
  traffic_used_gb: number | null
  traffic_remaining_pct: number | null
  provider: string
  status_from_panel: string
}

export interface UserProfile {
  user_id: number
  first_name: string
  last_name: string | null
  username: string | null
  photo_url: string | null
  language_code: string
  referral_code: string
  is_banned: boolean
  is_admin: boolean
  has_active_subscription: boolean
  subscription: ActiveSubscription | null
  trial_available: boolean
  links: {
    support: string
    docs: string
    reviews: string
    terms: string
    privacy: string
    instruction_ios: string
    instruction_android: string
    instruction_macos: string
    instruction_windows: string
    instruction_linux: string
  }
}

export interface AdminOverviewData {
  user_stats: {
    total_users: number
    banned_users: number
    active_today: number
    paid_subscriptions: number
    trial_users: number
    inactive_users: number
    referral_users: number
  }
  financial_stats: {
    today_revenue: number
    today_payments_count: number
    week_revenue: number
    month_revenue: number
    all_time_revenue: number
  }
  sync_status: {
    last_sync_time: string | null
    status: string
    details: string
    users_processed_from_panel: number
    subscriptions_synced: number
  }
  queue_stats: Record<string, unknown> | null
}

export interface AdminPromoItem {
  promo_code_id: number
  code: string
  promo_type: 'bonus_days' | 'discount'
  bonus_days: number
  discount_percentage: number
  max_activations: number
  current_activations: number
  is_active: boolean
  valid_until: string | null
}

export interface AdminUserItem {
  user_id: number
  username: string | null
  first_name: string | null
  avatar_url?: string | null
  is_banned: boolean
  registration_date: string | null
  total_spent?: number
  has_active_subscription?: boolean
}

export interface AdminAdItem {
  ad_campaign_id: number
  source: string
  start_param: string
  cost: number
  is_active: boolean
  created_at: string | null
}

export interface AdminLogItem {
  message_log_id: number
  user_id: number | null
  target_user_id: number | null
  telegram_username: string | null
  telegram_first_name: string | null
  event_type: string | null
  content: string | null
  timestamp: string | null
}

export interface AdminUserProfileData {
  user: {
    user_id: number
    username: string | null
    first_name: string | null
    last_name: string | null
    avatar_url: string | null
    is_banned: boolean
    registration_date: string | null
    panel_user_uuid: string | null
    referred_by_id: number | null
    total_spent: number
  }
  active_subscription: {
    subscription_id: number
    start_date: string | null
    end_date: string | null
    is_active: boolean
    status_from_panel: string | null
    duration_months: number | null
    traffic_limit_bytes: number | null
    traffic_used_bytes: number | null
  } | null
  subscriptions: Array<{
    subscription_id: number
    start_date: string | null
    end_date: string | null
    is_active: boolean
    duration_months: number | null
    provider: string | null
    status_from_panel: string | null
  }>
  payments: Array<{
    payment_id: number
    amount: number
    currency: string
    status: string
    provider: string | null
    description: string | null
    created_at: string | null
  }>
  devices: {
    items: Array<Record<string, unknown>>
    count: number
    max_devices: number | null
  }
}

export interface ChannelSubscriptionStatus {
  required: boolean
  subscribed: boolean
  channel_link: string
}

export interface SubscriptionPlan {
  months: number
  price_rub: number | null
  price_stars: number | null
  enabled: boolean
  is_popular: boolean
  is_best_value: boolean
}

export interface TrafficPackage {
  gb: number
  price_rub: number | null
  price_stars: number | null
}

export interface ActiveDiscount {
  discount_percentage: number
  promo_code: string
  expires_at: string
}

export interface PlansData {
  traffic_sale_mode: boolean
  plans: SubscriptionPlan[]
  traffic_packages: TrafficPackage[]
  included_traffic_gb: number | null
  max_devices: number | null
  active_discount: ActiveDiscount | null
  payment_methods: string[]
  trial_enabled: boolean
  trial_days: number
  trial_traffic_gb: number
  has_had_subscription: boolean
}

export interface LocationStatus {
  name: string
  country: string
  emoji: string
  status: 'online' | 'offline' | 'pending' | 'unknown'
  ping_ms: number | null
  uptime_pct: number | null
  availability: number[]
}

export interface ReferralBonus {
  inviter_days: number
  referee_days: number
}

export interface ReferralData {
  referral_code: string
  referral_link: string
  referred_count: number
  purchased_count: number
  bonus_structure: Record<string, ReferralBonus>
}

export type PromoType = 'bonus_days' | 'discount'

export interface PromoResult {
  success: boolean
  type?: PromoType
  bonus_days?: number
  new_end_date?: string
  discount_percentage?: number
  expires_at?: string
  error?: string
}

export interface PaymentResult {
  payment_id: string
  payment_url: string | null
  invoice_link: string | null
  provider: string
}

export type PaymentProvider =
  | 'yookassa'
  | 'stars'
  | 'cryptopay'
  | 'freekassa'
  | 'kassa_ai'
  | 'platega'
  | 'severpay'

export interface Device {
  hwid: string
  deviceModel: string | null
  platform: string | null
  osVersion: string | null
  createdAt: string | null
  userAgent: string | null
}

export interface DevicesData {
  devices: Device[]
  current_count: number
  max_devices: number | null
}

export interface ProxyItem {
  country: string
  emoji: string | null
  link: string
}

export type OperationType = 'trial_activated' | 'plan_payment'

export interface OperationHistoryItem {
  type: OperationType
  created_at: string | null
  end_date?: string | null
  duration_days?: number | null
  amount?: number
  currency?: string
  provider?: string
  months?: number | null
  description?: string
}

export interface OperationsHistoryData {
  operations: OperationHistoryItem[]
}

export interface ApiError {
  detail: string
  code?: string
}
