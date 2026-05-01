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
