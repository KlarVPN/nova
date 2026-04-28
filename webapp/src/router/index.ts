import { createRouter, createWebHashHistory } from 'vue-router'

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    {
      path: '/',
      component: () => import('@/views/HomeView.vue'),
      meta: { title: 'Home' },
    },
    {
      path: '/plans',
      component: () => import('@/views/PlansView.vue'),
      meta: { title: 'Plans' },
    },
    {
      path: '/referral',
      component: () => import('@/views/ReferralView.vue'),
      meta: { title: 'Referrals' },
    },
    {
      path: '/profile',
      component: () => import('@/views/ProfileView.vue'),
      meta: { title: 'Profile' },
    },
    {
      path: '/configs',
      component: () => import('@/views/ConfigsView.vue'),
      meta: { title: 'Configs' },
    },
    { path: '/promo', redirect: '/plans' },
  ],
  scrollBehavior: () => ({ top: 0 }),
})

export default router
