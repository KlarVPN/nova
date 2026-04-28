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
      name: 'configs',
      path: '/configs',
      component: () => import('@/views/ConfigsView.vue'),
      meta: { title: 'Configs' },
    },
    {
      name: 'faq',
      path: '/faq',
      component: () => import('@/views/FaqView.vue'),
      meta: { title: 'FAQ' },
    },
    { path: '/promo', redirect: '/plans' },
    { path: '/:pathMatch(.*)*', redirect: '/' },
  ],
  scrollBehavior: () => ({ top: 0 }),
})

export default router
