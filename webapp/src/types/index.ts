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
  language_code: string
  referral_code: string
  is_banned: boolean
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

export interface ApiError {
  detail: string
  code?: string
}
