import { createRouter, createWebHistory } from 'vue-router'
import { isTelegramWebApp } from '@/lib/telegram'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory('/app/'),
  routes: [
    {
      name: 'login',
      path: '/login',
      component: () => import('@/views/LoginView.vue'),
      meta: { public: true },
    },
    {
      name: 'th-auth',
      path: '/th/:uuid',
      component: () => import('@/views/AccessLinkAuthView.vue'),
      meta: { public: true },
    },
    {
      name: 'home',
      path: '/',
      component: () => import('@/views/HomeView.vue'),
      meta: { title: 'Home' },
    },
    {
      name: 'plans',
      path: '/plans',
      component: () => import('@/views/PlansView.vue'),
      meta: { title: 'Plans' },
    },
    {
      name: 'referral',
      path: '/referral',
      component: () => import('@/views/ReferralView.vue'),
      meta: { title: 'Referrals' },
    },
    {
      name: 'profile',
      path: '/profile',
      component: () => import('@/views/ProfileView.vue'),
      meta: { title: 'Profile' },
    },
    {
      name: 'access-save',
      path: '/access-save',
      component: () => import('@/views/AccessSaveView.vue'),
      meta: { title: 'Access Save' },
    },
    {
      name: 'setup',
      path: '/setup',
      component: () => import('@/views/SetupView.vue'),
      meta: { title: 'Setup' },
    },
    {
      name: 'faq',
      path: '/faq',
      component: () => import('@/views/FaqView.vue'),
      meta: { title: 'FAQ' },
    },
    {
      name: 'support',
      path: '/support',
      component: () => import('@/views/SupportView.vue'),
      meta: { title: 'Support' },
    },
    {
      name: 'support-setup',
      path: '/support/setup',
      component: () => import('@/views/SupportSetupView.vue'),
      meta: { title: 'Support Setup' },
    },
    {
      name: 'locations',
      path: '/locations',
      component: () => import('@/views/LocationsView.vue'),
      meta: { title: 'Locations' },
    },
    {
      name: 'proxies',
      path: '/proxies',
      component: () => import('@/views/ProxiesView.vue'),
      meta: { title: 'Proxies' },
    },
    {
      name: 'operations',
      path: '/operations',
      component: () => import('@/views/OperationsView.vue'),
      meta: { title: 'Operations' },
    },
    { path: '/configs', redirect: '/setup' },
    { path: '/promo', redirect: '/plans' },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
  scrollBehavior: () => ({ top: 0 }),
})

router.beforeEach(async (to) => {
  if (to.meta.public) return true

  const auth = useAuthStore()
  if (auth.isAuthenticated) return true

  if (isTelegramWebApp() || import.meta.env.DEV) {
    await auth.fetchProfile()
    if (auth.isAuthenticated) return true
    return { name: 'login' }
  }

  const token = localStorage.getItem('auth_token')
  if (!token) return { name: 'login' }

  await auth.fetchProfile()
  if (auth.isAuthenticated) return true

  auth.logout()
  return { name: 'login' }
})

export default router
