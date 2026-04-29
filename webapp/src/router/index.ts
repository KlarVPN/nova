import { createRouter, createWebHashHistory } from 'vue-router'

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
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

export default router
