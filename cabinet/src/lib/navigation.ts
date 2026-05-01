export type NavigationTab = {
  path: string
  label: string
  icon: string
}

export function getNavigationTabs(t: (key: string) => string): NavigationTab[] {
  return [
    { path: '/', label: t('nav.home'), icon: 'lucide:home' },
    { path: '/setup', label: t('nav.setup'), icon: 'lucide:settings' },
    { path: '/locations', label: t('nav.locations'), icon: 'lucide:map' },
    { path: '/profile', label: t('nav.profile'), icon: 'lucide:user' },
    { path: '/support', label: t('nav.support'), icon: 'lucide:headset' },
  ]
}

const profileNavPrefixes = [
  '/profile',
  '/plans',
  '/referral',
  '/faq',
  '/access-save',
  '/operations',
  '/proxies',
]

export function isNavTabActive(currentPath: string, tabPath: string): boolean {
  if (tabPath === '/') return currentPath === '/'
  if (tabPath === '/setup') return currentPath.startsWith('/setup')
  if (tabPath === '/locations') return currentPath.startsWith('/locations')
  if (tabPath === '/support') return currentPath.startsWith('/support')
  if (tabPath === '/profile') return profileNavPrefixes.some((prefix) => currentPath.startsWith(prefix))
  return currentPath === tabPath
}

export function getActiveNavPath(currentPath: string, tabPaths: string[]): string {
  return tabPaths.find((tabPath) => isNavTabActive(currentPath, tabPath)) ?? currentPath
}
