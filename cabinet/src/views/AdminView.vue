<script setup lang="ts">
import { PageHeroCard } from '@/components/common'
import { api } from '@/lib/api'
import { getAuthHeaders } from '@/lib/adminAuth'
import { useAuthStore } from '@/stores/auth'
import type { AdminAdItem, AdminLogItem, AdminOverviewData, AdminPromoItem, AdminUserItem, AdminUserProfileData } from '@/types'
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

type AdminTab = 'overview' | 'users' | 'payments' | 'promos' | 'ads' | 'logs' | 'broadcast'

const auth = useAuthStore()
const router = useRouter()
const { t } = useI18n()

const tabs: Array<{ id: AdminTab; label: string }> = [
  { id: 'overview', label: 'Overview' },
  { id: 'users', label: 'Users' },
  { id: 'payments', label: 'Payments' },
  { id: 'promos', label: 'Promos' },
  { id: 'ads', label: 'Ads' },
  { id: 'logs', label: 'Logs' },
  { id: 'broadcast', label: 'Broadcast' },
]

const activeTab = ref<AdminTab>('overview')
const loading = ref(false)
const busy = ref(false)
const error = ref('')
const note = ref('')

const overview = ref<AdminOverviewData | null>(null)

const users = ref<AdminUserItem[]>([])
const usersTotal = ref(0)
const usersPage = ref(0)
const usersSearch = ref('')
const usersOnlyActive = ref<boolean | null>(null)
const usersRegisteredFrom = ref('')
const usersRegisteredTo = ref('')
const usersMinSpent = ref('')
const usersMaxSpent = ref('')
const selectedUserProfile = ref<AdminUserProfileData | null>(null)
const showUserProfile = ref(false)
const userMessageText = ref('')
const userSubDeltaDays = ref('30')
const userRegeneratedLink = ref('')
const usersLoadingMore = ref(false)
const usersHasMore = ref(true)
const usersSentinel = ref<HTMLElement | null>(null)
let usersObserver: IntersectionObserver | null = null

const payments = ref<Array<{ payment_id: number; user_id: number; username: string | null; amount: number; currency: string; status: string; provider: string | null; created_at: string | null }>>([])
const paymentsTotal = ref(0)
const paymentsPage = ref(0)

const promos = ref<AdminPromoItem[]>([])
const promosTotal = ref(0)
const promosPage = ref(0)
const promosSearch = ref('')

const ads = ref<AdminAdItem[]>([])
const adsTotal = ref(0)
const adsPage = ref(0)
const adsSearch = ref('')

const logs = ref<AdminLogItem[]>([])
const logsTotal = ref(0)
const logsPage = ref(0)
const logsSearch = ref('')

const broadcastText = ref('')
const broadcastTarget = ref<'all' | 'active' | 'inactive'>('all')

const newPromoCode = ref('')
const newPromoType = ref<'bonus_days' | 'discount'>('bonus_days')
const newPromoValue = ref('30')
const newPromoMax = ref('1')

const newAdSource = ref('')
const newAdParam = ref('')
const newAdCost = ref('0')

const canSendBroadcast = computed(() => broadcastText.value.trim().length > 0)
const confirmDeletePromo = ref<AdminPromoItem | null>(null)
const confirmDeleteAd = ref<AdminAdItem | null>(null)

const filteredUsers = computed(() => {
  const q = usersSearch.value.trim().toLowerCase()
  if (!q) return users.value
  return users.value.filter((u) =>
    [String(u.user_id), u.first_name ?? '', u.username ?? ''].join(' ').toLowerCase().includes(q),
  )
})

const filteredPromos = computed(() => {
  const q = promosSearch.value.trim().toLowerCase()
  if (!q) return promos.value
  return promos.value.filter((p) => p.code.toLowerCase().includes(q))
})

const filteredAds = computed(() => {
  const q = adsSearch.value.trim().toLowerCase()
  if (!q) return ads.value
  return ads.value.filter((a) => `${a.source} ${a.start_param}`.toLowerCase().includes(q))
})

const filteredLogs = computed(() => {
  const q = logsSearch.value.trim().toLowerCase()
  if (!q) return logs.value
  return logs.value.filter((l) => `${l.event_type ?? ''} ${l.content ?? ''}`.toLowerCase().includes(q))
})

function setNote(message: string) {
  note.value = message
  setTimeout(() => {
    if (note.value === message) note.value = ''
  }, 2500)
}

function formatDate(value: string | null): string {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '—'
  return new Intl.DateTimeFormat('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}

async function runAction(action: () => Promise<void>) {
  busy.value = true
  error.value = ''
  try {
    await action()
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Operation failed'
  } finally {
    busy.value = false
  }
}

async function loadOverview() {
  overview.value = await api.admin.overview()
}

async function loadUsers(append = false) {
  const response = await api.admin.users({
    page: usersPage.value,
    pageSize: 20,
    q: usersSearch.value.trim() || undefined,
    hasActiveSubscription: usersOnlyActive.value === null ? undefined : usersOnlyActive.value,
    registeredFrom: usersRegisteredFrom.value || undefined,
    registeredTo: usersRegisteredTo.value || undefined,
    minSpent: usersMinSpent.value ? Number(usersMinSpent.value) : undefined,
    maxSpent: usersMaxSpent.value ? Number(usersMaxSpent.value) : undefined,
    sortBy: 'registration_date',
    sortOrder: 'desc',
  })
  users.value = append ? [...users.value, ...response.items] : response.items
  usersTotal.value = response.total
  usersHasMore.value = response.has_more
}

async function loadMoreUsers() {
  if (usersLoadingMore.value || !usersHasMore.value || activeTab.value !== 'users') return
  usersLoadingMore.value = true
  try {
    usersPage.value += 1
    await loadUsers(true)
  } finally {
    usersLoadingMore.value = false
  }
}

async function resetUsersFeed() {
  usersPage.value = 0
  usersHasMore.value = true
  await loadUsers(false)
}

async function loadPayments() {
  const response = await api.admin.payments(paymentsPage.value, 20)
  payments.value = response.items
  paymentsTotal.value = response.total
}

async function loadPromos() {
  const response = await api.admin.promos(promosPage.value, 20)
  promos.value = response.items
  promosTotal.value = response.total
}

async function loadAds() {
  const response = await api.admin.ads(adsPage.value, 20)
  ads.value = response.items
  adsTotal.value = response.total
}

async function loadLogs() {
  const response = await api.admin.logs(logsPage.value, 50)
  logs.value = response.items
  logsTotal.value = response.total
}

async function syncPanel() {
  await runAction(async () => {
    await api.admin.sync()
    await loadOverview()
    setNote('Sync completed')
  })
}

async function toggleBan(user: AdminUserItem) {
  await runAction(async () => {
    if (user.is_banned) await api.admin.unbanUser(user.user_id)
    else await api.admin.banUser(user.user_id)
    await resetUsersFeed()
  })
}

async function openUserProfile(user: AdminUserItem) {
  await runAction(async () => {
    selectedUserProfile.value = await api.admin.userProfile(user.user_id)
    userMessageText.value = ''
    userSubDeltaDays.value = '30'
    userRegeneratedLink.value = ''
    showUserProfile.value = true
  })
}

async function sendUserMessage() {
  if (!selectedUserProfile.value) return
  const text = userMessageText.value.trim()
  if (!text) return
  await runAction(async () => {
    await api.admin.messageUser(selectedUserProfile.value!.user.user_id, text)
    userMessageText.value = ''
    setNote('Message sent')
  })
}

async function applySubscriptionDeltaDays() {
  if (!selectedUserProfile.value) return
  const days = Number(userSubDeltaDays.value || 0)
  if (!days) return
  await runAction(async () => {
    await api.admin.changeUserSubscriptionDays(selectedUserProfile.value!.user.user_id, days)
    selectedUserProfile.value = await api.admin.userProfile(selectedUserProfile.value!.user.user_id)
    setNote('Subscription period updated')
  })
}

async function applyDeviceLimit(limit: number) {
  if (!selectedUserProfile.value) return
  await runAction(async () => {
    await api.admin.setUserDevicesLimit(selectedUserProfile.value!.user.user_id, limit)
    selectedUserProfile.value = await api.admin.userProfile(selectedUserProfile.value!.user.user_id)
    setNote('Device limit updated')
  })
}

async function applyTrafficLimit(gb: number | null, unlimited = false) {
  if (!selectedUserProfile.value) return
  await runAction(async () => {
    await api.admin.setUserTrafficLimit(selectedUserProfile.value!.user.user_id, gb, unlimited)
    selectedUserProfile.value = await api.admin.userProfile(selectedUserProfile.value!.user.user_id)
    setNote('Traffic limit updated')
  })
}

async function resetUserHwidAction() {
  if (!selectedUserProfile.value) return
  await runAction(async () => {
    const result = await api.admin.resetUserHwid(selectedUserProfile.value!.user.user_id)
    selectedUserProfile.value = await api.admin.userProfile(selectedUserProfile.value!.user.user_id)
    setNote(`HWID reset: ${result.disconnected} devices`)
  })
}

async function regenerateUserLink() {
  if (!selectedUserProfile.value) return
  await runAction(async () => {
    const result = await api.admin.regenerateUserSubscriptionLink(selectedUserProfile.value!.user.user_id)
    userRegeneratedLink.value = result.subscription_url
    setNote('Subscription link regenerated')
  })
}

async function syncUserAction() {
  if (!selectedUserProfile.value) return
  await runAction(async () => {
    await api.admin.syncUser(selectedUserProfile.value!.user.user_id)
    selectedUserProfile.value = await api.admin.userProfile(selectedUserProfile.value!.user.user_id)
    setNote('User synced with panel')
  })
}

async function createPromo() {
  await runAction(async () => {
    const payload: Record<string, unknown> = {
      code: newPromoCode.value.trim(),
      promo_type: newPromoType.value,
      max_activations: Number(newPromoMax.value || 1),
    }
    if (newPromoType.value === 'bonus_days') payload.bonus_days = Number(newPromoValue.value || 0)
    else payload.discount_percentage = Number(newPromoValue.value || 0)
    await api.admin.createPromo(payload)
    newPromoCode.value = ''
    await loadPromos()
  })
}

async function togglePromo(item: AdminPromoItem) {
  await runAction(async () => {
    await api.admin.updatePromo(item.promo_code_id, { is_active: !item.is_active })
    await loadPromos()
  })
}

async function removePromo(item: AdminPromoItem) {
  await runAction(async () => {
    await api.admin.deletePromo(item.promo_code_id)
    await loadPromos()
    confirmDeletePromo.value = null
  })
}

async function exportPromoCsv(item: AdminPromoItem) {
  const response = await fetch(api.admin.promoActivationsCsvUrl(item.promo_code_id), {
    headers: getAuthHeaders(),
  })
  if (!response.ok) throw new Error('Failed to export promo CSV')
  const blob = await response.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `promo_${item.code}_activations.csv`
  a.click()
  URL.revokeObjectURL(url)
}

async function createAd() {
  await runAction(async () => {
    await api.admin.createAd({
      source: newAdSource.value.trim(),
      start_param: newAdParam.value.trim(),
      cost: Number(newAdCost.value || 0),
    })
    newAdSource.value = ''
    newAdParam.value = ''
    newAdCost.value = '0'
    await loadAds()
  })
}

async function toggleAd(item: AdminAdItem) {
  await runAction(async () => {
    await api.admin.toggleAd(item.ad_campaign_id, !item.is_active)
    await loadAds()
  })
}

async function removeAd(item: AdminAdItem) {
  await runAction(async () => {
    await api.admin.deleteAd(item.ad_campaign_id)
    await loadAds()
    confirmDeleteAd.value = null
  })
}

async function sendBroadcast() {
  await runAction(async () => {
    const response = await api.admin.broadcast(broadcastText.value.trim(), broadcastTarget.value)
    broadcastText.value = ''
    setNote(`Queued: ${response.queued}`)
  })
}

async function exportPaymentsCsv() {
  const response = await fetch(api.admin.paymentsCsvUrl(), { headers: getAuthHeaders() })
  if (!response.ok) throw new Error('Failed to export payments CSV')
  const blob = await response.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'payments_export.csv'
  a.click()
  URL.revokeObjectURL(url)
}

onMounted(async () => {
  if (!auth.profile?.is_admin) {
    await router.replace('/')
    return
  }
  loading.value = true
  try {
    await Promise.all([
      loadOverview(),
      resetUsersFeed(),
      loadPayments(),
      loadPromos(),
      loadAds(),
      loadLogs(),
    ])

    usersObserver = new IntersectionObserver(
      (entries) => {
        const first = entries[0]
        if (first?.isIntersecting) {
          void loadMoreUsers()
        }
      },
      { rootMargin: '220px 0px' },
    )

    await nextTick()
    if (usersSentinel.value) usersObserver.observe(usersSentinel.value)
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Failed to load admin dashboard'
  } finally {
    loading.value = false
  }
})

watch(activeTab, async (tab) => {
  if (tab !== 'users') return
  await nextTick()
  if (usersSentinel.value && usersObserver) {
    usersObserver.disconnect()
    usersObserver.observe(usersSentinel.value)
  }
})

watch(usersSearch, async () => {
  if (activeTab.value !== 'users') return
  await resetUsersFeed()
})

watch(usersOnlyActive, async () => {
  if (activeTab.value !== 'users') return
  await resetUsersFeed()
})

watch([usersRegisteredFrom, usersRegisteredTo, usersMinSpent, usersMaxSpent], async () => {
  if (activeTab.value !== 'users') return
  await resetUsersFeed()
})

onBeforeUnmount(() => {
  usersObserver?.disconnect()
  usersObserver = null
})
</script>

<template>
  <div class="mx-auto flex w-full max-w-5xl flex-col gap-4 pt-2 pb-6">
    <PageHeroCard :title="t('admin.title')" :description="t('admin.subtitle')" icon="lucide:shield-check" />
    <div class="sticky top-2 z-30 flex flex-wrap gap-2 rounded-[14px] border border-neutral-900 bg-neutral-950/95 p-2 text-xs backdrop-blur">
      <button v-for="tab in tabs" :key="tab.id" type="button" class="rounded-lg px-3 py-2" :class="activeTab === tab.id ? 'bg-white text-black' : 'text-neutral-300 hover:bg-neutral-900'" @click="activeTab = tab.id">{{ t(`admin.tabs.${tab.id}`) }}</button>
    </div>
    <div v-if="note" class="rounded-[14px] border border-emerald-800 bg-emerald-950/30 px-4 py-3 text-sm text-emerald-200">{{ note }}</div>
    <div v-if="loading" class="rounded-[14px] bg-neutral-950 px-4 py-6 text-sm text-neutral-400">{{ t('common.loading') }}</div>
    <div v-else-if="error" class="rounded-[14px] bg-red-950/50 px-4 py-6 text-sm text-red-200">{{ error }}</div>
    <template v-else>
      <template v-if="activeTab === 'overview' && overview">
        <div class="grid grid-cols-2 gap-2 md:grid-cols-4">
          <div class="rounded-[14px] bg-neutral-950 px-4 py-3"><p class="text-xs text-neutral-500">{{ t('admin.metrics.users') }}</p><p class="text-xl font-semibold text-white">{{ overview.user_stats.total_users }}</p></div>
          <div class="rounded-[14px] bg-neutral-950 px-4 py-3"><p class="text-xs text-neutral-500">{{ t('admin.metrics.banned') }}</p><p class="text-xl font-semibold text-white">{{ overview.user_stats.banned_users }}</p></div>
          <div class="rounded-[14px] bg-neutral-950 px-4 py-3"><p class="text-xs text-neutral-500">{{ t('admin.metrics.revenueToday') }}</p><p class="text-xl font-semibold text-white">{{ overview.financial_stats.today_revenue.toFixed(2) }}</p></div>
          <div class="rounded-[14px] bg-neutral-950 px-4 py-3"><p class="text-xs text-neutral-500">{{ t('admin.metrics.revenueAll') }}</p><p class="text-xl font-semibold text-white">{{ overview.financial_stats.all_time_revenue.toFixed(2) }}</p></div>
        </div>
        <div class="rounded-[14px] bg-neutral-950 px-4 py-4"><button type="button" class="rounded-lg bg-white px-3 py-2 text-sm text-black disabled:opacity-60" :disabled="busy" @click="syncPanel">{{ t('admin.actions.runSync') }}</button></div>
      </template>

      <template v-if="activeTab === 'users'">
        <div class="flex items-center gap-2 rounded-[14px] bg-neutral-950 p-2">
          <input v-model="usersSearch" class="w-full rounded bg-neutral-900 px-3 py-2 text-sm text-white" :placeholder="t('admin.search.users')" />
          <input v-model="usersRegisteredFrom" type="date" class="rounded bg-neutral-900 px-2 py-2 text-xs text-white" />
          <input v-model="usersRegisteredTo" type="date" class="rounded bg-neutral-900 px-2 py-2 text-xs text-white" />
          <input v-model="usersMinSpent" class="w-24 rounded bg-neutral-900 px-2 py-2 text-xs text-white" placeholder="Min spent" />
          <input v-model="usersMaxSpent" class="w-24 rounded bg-neutral-900 px-2 py-2 text-xs text-white" placeholder="Max spent" />
          <button type="button" class="rounded px-3 py-2 text-xs" :class="usersOnlyActive === true ? 'bg-white text-black' : 'bg-neutral-800 text-white'" @click="usersOnlyActive = usersOnlyActive === true ? null : true">Active</button>
          <button type="button" class="rounded px-3 py-2 text-xs" :class="usersOnlyActive === false ? 'bg-white text-black' : 'bg-neutral-800 text-white'" @click="usersOnlyActive = usersOnlyActive === false ? null : false">Inactive</button>
          <button type="button" class="rounded bg-neutral-800 px-3 py-2 text-xs text-white" @click="usersSearch = ''; usersRegisteredFrom = ''; usersRegisteredTo = ''; usersMinSpent = ''; usersMaxSpent = ''; usersOnlyActive = null">Reset</button>
        </div>
        <p class="text-xs text-neutral-400">Total: {{ usersTotal }}</p>
        <div v-for="u in filteredUsers" :key="u.user_id" class="rounded-[14px] bg-neutral-950 px-4 py-3 cursor-pointer" @click="openUserProfile(u)">
          <div class="flex items-center gap-3">
            <img
              v-if="u.avatar_url"
              :src="u.avatar_url"
              alt="avatar"
              class="size-10 rounded-full object-cover"
            />
            <div v-else class="flex size-10 items-center justify-center rounded-full bg-neutral-800 text-xs text-neutral-300">
              {{ (u.first_name || u.username || 'U').slice(0, 1).toUpperCase() }}
            </div>

            <div class="min-w-0 flex-1">
              <p class="truncate text-sm text-white">{{ u.first_name || `User ${u.user_id}` }}</p>
              <p class="truncate text-xs text-neutral-400">{{ u.username ? `@${u.username}` : '—' }}</p>
              <p class="text-xs text-neutral-500">ID {{ u.user_id }}</p>
              <p class="text-xs text-neutral-500">Spent: {{ u.total_spent ?? 0 }}</p>
            </div>

            <button
              type="button"
              class="rounded bg-white px-2 py-1 text-xs text-black"
              :disabled="busy"
              @click.stop="toggleBan(u)"
            >
              {{ u.is_banned ? t('admin.actions.unban') : t('admin.actions.ban') }}
            </button>
          </div>
        </div>
        <div ref="usersSentinel" class="h-6" />
        <p v-if="usersLoadingMore" class="text-center text-xs text-neutral-500">{{ t('common.loading') }}</p>
        <p v-else-if="!usersHasMore" class="text-center text-xs text-neutral-600">No more users</p>
      </template>

      <template v-if="activeTab === 'payments'">
        <div class="flex items-center gap-2 rounded-[14px] bg-neutral-950 p-2"><button type="button" class="rounded bg-white px-3 py-2 text-xs text-black" @click="exportPaymentsCsv">{{ t('admin.actions.exportCsv') }}</button><button type="button" class="rounded bg-neutral-800 px-3 py-2 text-xs text-white" :disabled="paymentsPage===0" @click="paymentsPage--; loadPayments()">{{ t('admin.actions.prev') }}</button><button type="button" class="rounded bg-neutral-800 px-3 py-2 text-xs text-white" @click="paymentsPage++; loadPayments()">{{ t('admin.actions.next') }}</button></div>
        <p class="text-xs text-neutral-400">Total: {{ paymentsTotal }}</p>
        <div class="overflow-x-auto rounded-[14px] border border-neutral-900 bg-neutral-950">
          <table class="w-full min-w-[680px] text-left text-xs">
            <thead class="sticky top-0 bg-neutral-950 text-neutral-500"><tr><th class="px-3 py-2">ID</th><th class="px-3 py-2">User</th><th class="px-3 py-2">Amount</th><th class="px-3 py-2">Provider</th><th class="px-3 py-2">Status</th><th class="px-3 py-2">Date</th></tr></thead>
            <tbody>
              <tr v-for="p in payments" :key="p.payment_id" class="border-t border-neutral-900">
                <td class="px-3 py-2 text-white">#{{ p.payment_id }}</td><td class="px-3 py-2 text-white">{{ p.user_id }}</td><td class="px-3 py-2 text-white">{{ p.amount }} {{ p.currency }}</td><td class="px-3 py-2 text-neutral-300">{{ p.provider || 'unknown' }}</td><td class="px-3 py-2 text-neutral-300">{{ p.status }}</td><td class="px-3 py-2 text-neutral-300">{{ formatDate(p.created_at) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </template>

      <template v-if="activeTab === 'promos'">
        <div class="flex items-center gap-2 rounded-[14px] bg-neutral-950 p-2">
          <input v-model="promosSearch" class="w-full rounded bg-neutral-900 px-3 py-2 text-sm text-white" :placeholder="t('admin.search.promos')" />
          <button type="button" class="rounded bg-neutral-800 px-3 py-2 text-xs text-white" @click="promosSearch = ''">Reset</button>
        </div>
        <div class="rounded-[14px] bg-neutral-950 px-4 py-3"><div class="grid grid-cols-2 gap-2"><input v-model="newPromoCode" class="rounded bg-neutral-900 px-2 py-2 text-sm text-white" placeholder="Code" /><select v-model="newPromoType" class="rounded bg-neutral-900 px-2 py-2 text-sm text-white"><option value="bonus_days">bonus_days</option><option value="discount">discount</option></select><input v-model="newPromoValue" class="rounded bg-neutral-900 px-2 py-2 text-sm text-white" :placeholder="newPromoType==='bonus_days'?'Bonus days':'Discount %'" /><input v-model="newPromoMax" class="rounded bg-neutral-900 px-2 py-2 text-sm text-white" placeholder="Max activations" /></div><button type="button" class="mt-2 rounded bg-white px-3 py-2 text-sm text-black" :disabled="busy" @click="createPromo">Create promo</button></div>
        <div class="flex items-center gap-2"><button type="button" class="rounded bg-neutral-800 px-3 py-2 text-xs text-white" :disabled="promosPage===0" @click="promosPage--; loadPromos()">{{ t('admin.actions.prev') }}</button><button type="button" class="rounded bg-neutral-800 px-3 py-2 text-xs text-white" @click="promosPage++; loadPromos()">{{ t('admin.actions.next') }}</button></div>
        <p class="text-xs text-neutral-400">Total: {{ promosTotal }}</p>
        <div v-for="p in filteredPromos" :key="p.promo_code_id" class="rounded-[14px] bg-neutral-950 px-4 py-3"><p class="text-sm text-white">{{ p.code }} ({{ p.promo_type }})</p><div class="mt-2 flex gap-2"><button type="button" class="rounded bg-white px-2 py-1 text-xs text-black" :disabled="busy" @click="togglePromo(p)">{{ p.is_active ? t('admin.actions.disable') : t('admin.actions.enable') }}</button><button type="button" class="rounded bg-neutral-700 px-2 py-1 text-xs text-white" :disabled="busy" @click="exportPromoCsv(p)">CSV</button><button type="button" class="rounded bg-red-500 px-2 py-1 text-xs text-white" :disabled="busy" @click="confirmDeletePromo = p">{{ t('admin.actions.delete') }}</button></div></div>
      </template>

      <template v-if="activeTab === 'ads'">
        <div class="flex items-center gap-2 rounded-[14px] bg-neutral-950 p-2">
          <input v-model="adsSearch" class="w-full rounded bg-neutral-900 px-3 py-2 text-sm text-white" :placeholder="t('admin.search.ads')" />
          <button type="button" class="rounded bg-neutral-800 px-3 py-2 text-xs text-white" @click="adsSearch = ''">Reset</button>
        </div>
        <div class="rounded-[14px] bg-neutral-950 px-4 py-3"><div class="grid grid-cols-3 gap-2"><input v-model="newAdSource" class="rounded bg-neutral-900 px-2 py-2 text-sm text-white" placeholder="Source" /><input v-model="newAdParam" class="rounded bg-neutral-900 px-2 py-2 text-sm text-white" placeholder="Start param" /><input v-model="newAdCost" class="rounded bg-neutral-900 px-2 py-2 text-sm text-white" placeholder="Cost" /></div><button type="button" class="mt-2 rounded bg-white px-3 py-2 text-sm text-black" :disabled="busy" @click="createAd">Create campaign</button></div>
        <div class="flex items-center gap-2"><button type="button" class="rounded bg-neutral-800 px-3 py-2 text-xs text-white" :disabled="adsPage===0" @click="adsPage--; loadAds()">{{ t('admin.actions.prev') }}</button><button type="button" class="rounded bg-neutral-800 px-3 py-2 text-xs text-white" @click="adsPage++; loadAds()">{{ t('admin.actions.next') }}</button></div>
        <p class="text-xs text-neutral-400">Total: {{ adsTotal }}</p>
        <div v-for="c in filteredAds" :key="c.ad_campaign_id" class="rounded-[14px] bg-neutral-950 px-4 py-3"><p class="text-sm text-white">{{ c.source }} / {{ c.start_param }}</p><div class="mt-2 flex gap-2"><button type="button" class="rounded bg-white px-2 py-1 text-xs text-black" :disabled="busy" @click="toggleAd(c)">{{ c.is_active ? t('admin.actions.disable') : t('admin.actions.enable') }}</button><button type="button" class="rounded bg-red-500 px-2 py-1 text-xs text-white" :disabled="busy" @click="confirmDeleteAd = c">{{ t('admin.actions.delete') }}</button></div></div>
      </template>

      <template v-if="activeTab === 'logs'">
        <div class="flex items-center gap-2 rounded-[14px] bg-neutral-950 p-2">
          <input v-model="logsSearch" class="w-full rounded bg-neutral-900 px-3 py-2 text-sm text-white" :placeholder="t('admin.search.logs')" />
          <button type="button" class="rounded bg-neutral-800 px-3 py-2 text-xs text-white" @click="logsSearch = ''">Reset</button>
        </div>
        <div class="flex items-center gap-2"><button type="button" class="rounded bg-neutral-800 px-3 py-2 text-xs text-white" :disabled="logsPage===0" @click="logsPage--; loadLogs()">{{ t('admin.actions.prev') }}</button><button type="button" class="rounded bg-neutral-800 px-3 py-2 text-xs text-white" @click="logsPage++; loadLogs()">{{ t('admin.actions.next') }}</button></div>
        <p class="text-xs text-neutral-400">Total: {{ logsTotal }}</p>
        <div v-for="l in filteredLogs" :key="l.message_log_id" class="rounded-[14px] bg-neutral-950 px-4 py-3"><p class="text-xs text-neutral-500">{{ l.timestamp || 'N/A' }}</p><p class="text-sm text-white">{{ l.event_type || 'event' }}</p><p class="text-xs text-neutral-400">{{ l.content || '—' }}</p></div>
      </template>

      <template v-if="activeTab === 'broadcast'">
        <div class="rounded-[14px] bg-neutral-950 px-4 py-3"><textarea v-model="broadcastText" class="h-28 w-full rounded bg-neutral-900 px-2 py-2 text-sm text-white" :placeholder="t('admin.broadcastPlaceholder')" /><div class="mt-2 flex gap-2"><button type="button" class="rounded px-2 py-1 text-xs" :class="broadcastTarget==='all' ? 'bg-white text-black' : 'bg-neutral-800 text-white'" @click="broadcastTarget='all'">{{ t('admin.target.all') }}</button><button type="button" class="rounded px-2 py-1 text-xs" :class="broadcastTarget==='active' ? 'bg-white text-black' : 'bg-neutral-800 text-white'" @click="broadcastTarget='active'">{{ t('admin.target.active') }}</button><button type="button" class="rounded px-2 py-1 text-xs" :class="broadcastTarget==='inactive' ? 'bg-white text-black' : 'bg-neutral-800 text-white'" @click="broadcastTarget='inactive'">{{ t('admin.target.inactive') }}</button></div><button type="button" class="mt-2 rounded bg-white px-3 py-2 text-sm text-black disabled:opacity-60" :disabled="busy || !canSendBroadcast" @click="sendBroadcast">{{ t('admin.actions.sendBroadcast') }}</button></div>
      </template>

      <div v-if="confirmDeletePromo" class="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
        <div class="w-full max-w-sm rounded-[14px] bg-neutral-950 p-4">
          <p class="text-sm text-white">{{ t('admin.confirmDeletePromo', { code: confirmDeletePromo.code }) }}</p>
          <div class="mt-3 flex gap-2"><button type="button" class="rounded bg-neutral-800 px-3 py-2 text-xs text-white" @click="confirmDeletePromo = null">{{ t('admin.actions.cancel') }}</button><button type="button" class="rounded bg-red-600 px-3 py-2 text-xs text-white" :disabled="busy" @click="removePromo(confirmDeletePromo)">{{ t('admin.actions.delete') }}</button></div>
        </div>
      </div>

      <div v-if="confirmDeleteAd" class="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
        <div class="w-full max-w-sm rounded-[14px] bg-neutral-950 p-4">
          <p class="text-sm text-white">{{ t('admin.confirmDeleteAd', { source: confirmDeleteAd.source }) }}</p>
          <div class="mt-3 flex gap-2"><button type="button" class="rounded bg-neutral-800 px-3 py-2 text-xs text-white" @click="confirmDeleteAd = null">{{ t('admin.actions.cancel') }}</button><button type="button" class="rounded bg-red-600 px-3 py-2 text-xs text-white" :disabled="busy" @click="removeAd(confirmDeleteAd)">{{ t('admin.actions.delete') }}</button></div>
        </div>
      </div>

      <div v-if="showUserProfile && selectedUserProfile" class="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4" @click.self="showUserProfile = false">
        <div class="w-full max-w-2xl rounded-[14px] bg-neutral-950 p-4">
          <div class="flex items-start gap-3">
            <img v-if="selectedUserProfile.user.avatar_url" :src="selectedUserProfile.user.avatar_url" class="size-12 rounded-full object-cover" />
            <div v-else class="flex size-12 items-center justify-center rounded-full bg-neutral-800 text-sm text-neutral-300">U</div>
            <div class="min-w-0 flex-1">
              <p class="text-base font-semibold text-white">{{ selectedUserProfile.user.first_name || 'User' }}</p>
              <p class="text-xs text-neutral-400">{{ selectedUserProfile.user.username ? `@${selectedUserProfile.user.username}` : '—' }} · ID {{ selectedUserProfile.user.user_id }}</p>
              <p class="text-xs text-neutral-500">Spent: {{ selectedUserProfile.user.total_spent }}</p>
            </div>
            <button type="button" class="rounded bg-neutral-800 px-2 py-1 text-xs text-white" @click="showUserProfile = false">Close</button>
          </div>

          <div class="mt-4 grid grid-cols-2 gap-2 text-xs">
            <div class="rounded bg-neutral-900 px-3 py-2 text-neutral-300">Devices: {{ selectedUserProfile.devices.count }} / {{ selectedUserProfile.devices.max_devices ?? '∞' }}</div>
            <div class="rounded bg-neutral-900 px-3 py-2 text-neutral-300">Subs history: {{ selectedUserProfile.subscriptions.length }}</div>
          </div>

          <div class="mt-3 rounded bg-neutral-900 p-3">
            <p class="mb-2 text-xs text-neutral-400">Send personal message</p>
            <textarea v-model="userMessageText" class="h-20 w-full rounded bg-neutral-800 px-2 py-2 text-sm text-white" placeholder="Message text" />
            <button type="button" class="mt-2 rounded bg-white px-3 py-2 text-xs text-black" :disabled="busy" @click="sendUserMessage">Send</button>
          </div>

          <div class="mt-3 rounded bg-neutral-900 p-3">
            <p class="mb-2 text-xs text-neutral-400">Subscription actions</p>
            <div class="flex flex-wrap items-center gap-2">
              <input v-model="userSubDeltaDays" class="w-24 rounded bg-neutral-800 px-2 py-2 text-xs text-white" placeholder="days" />
              <button type="button" class="rounded bg-white px-2 py-2 text-xs text-black" :disabled="busy" @click="applySubscriptionDeltaDays">Apply days</button>
              <button type="button" class="rounded bg-neutral-800 px-2 py-2 text-xs text-white" :disabled="busy" @click="userSubDeltaDays = '30'; applySubscriptionDeltaDays()">+30</button>
              <button type="button" class="rounded bg-neutral-800 px-2 py-2 text-xs text-white" :disabled="busy" @click="userSubDeltaDays = '-30'; applySubscriptionDeltaDays()">-30</button>
            </div>
          </div>

          <div class="mt-3 rounded bg-neutral-900 p-3">
            <p class="mb-2 text-xs text-neutral-400">Device / traffic limits</p>
            <div class="flex flex-wrap items-center gap-2">
              <button v-for="n in [1,2,3,5,10]" :key="`dev-${n}`" type="button" class="rounded bg-neutral-800 px-2 py-1 text-xs text-white" :disabled="busy" @click="applyDeviceLimit(n)">{{ n }} devices</button>
            </div>
            <div class="mt-2 flex flex-wrap items-center gap-2">
              <button v-for="gb in [50,100,500,1000]" :key="`gb-${gb}`" type="button" class="rounded bg-neutral-800 px-2 py-1 text-xs text-white" :disabled="busy" @click="applyTrafficLimit(gb)">{{ gb }} GB</button>
              <button type="button" class="rounded bg-neutral-700 px-2 py-1 text-xs text-white" :disabled="busy" @click="applyTrafficLimit(null, true)">Unlimited</button>
            </div>
          </div>

          <div class="mt-3 rounded bg-neutral-900 p-3">
            <p class="mb-2 text-xs text-neutral-400">Maintenance actions</p>
            <div class="flex flex-wrap gap-2">
              <button type="button" class="rounded bg-neutral-800 px-2 py-2 text-xs text-white" :disabled="busy" @click="resetUserHwidAction">Reset HWID</button>
              <button type="button" class="rounded bg-neutral-800 px-2 py-2 text-xs text-white" :disabled="busy" @click="regenerateUserLink">Regenerate link</button>
              <button type="button" class="rounded bg-neutral-800 px-2 py-2 text-xs text-white" :disabled="busy" @click="syncUserAction">Sync user</button>
            </div>
            <div v-if="userRegeneratedLink" class="mt-2 rounded bg-neutral-800 px-2 py-2 text-xs text-neutral-200 break-all">
              {{ userRegeneratedLink }}
            </div>
          </div>

          <div class="mt-3 rounded bg-neutral-900 p-3">
            <p class="mb-2 text-xs text-neutral-400">Recent payments</p>
            <div class="max-h-40 overflow-auto text-xs text-neutral-300">
              <div v-for="p in selectedUserProfile.payments" :key="p.payment_id" class="border-b border-neutral-800 py-1">
                #{{ p.payment_id }} · {{ p.amount }} {{ p.currency }} · {{ p.status }} · {{ formatDate(p.created_at) }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>
