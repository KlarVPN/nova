interface TelegramWebApp {
  initData: string
  initDataUnsafe: {
    user?: {
      id: number
      first_name: string
      last_name?: string
      username?: string
      language_code?: string
      photo_url?: string
    }
    start_param?: string
    auth_date: number
    hash: string
  }
  version: string
  platform: string
  colorScheme: 'light' | 'dark'
  themeParams: {
    bg_color?: string
    text_color?: string
    hint_color?: string
    link_color?: string
    button_color?: string
    button_text_color?: string
  }
  isExpanded: boolean
  viewportHeight: number
  viewportStableHeight: number
  headerColor: string
  backgroundColor: string
  isClosingConfirmationEnabled: boolean
  BackButton: {
    isVisible: boolean
    onClick(fn: () => void): void
    offClick(fn: () => void): void
    show(): void
    hide(): void
  }
  MainButton: {
    text: string
    color: string
    textColor: string
    isVisible: boolean
    isProgressVisible: boolean
    isActive: boolean
    setText(text: string): void
    onClick(fn: () => void): void
    offClick(fn: () => void): void
    show(): void
    hide(): void
    enable(): void
    disable(): void
    showProgress(leaveActive?: boolean): void
    hideProgress(): void
  }
  HapticFeedback: {
    impactOccurred(style: 'light' | 'medium' | 'heavy' | 'rigid' | 'soft'): void
    notificationOccurred(type: 'error' | 'success' | 'warning'): void
    selectionChanged(): void
  }
  expand(): void
  close(): void
  ready(): void
  sendData(data: string): void
  openLink(url: string, options?: { try_instant_view?: boolean }): void
  openTelegramLink(url: string): void
  openInvoice(url: string, callback?: (status: 'paid' | 'cancelled' | 'failed' | 'pending') => void): void
  showAlert(message: string, callback?: () => void): void
  showConfirm(message: string, callback: (confirmed: boolean) => void): void
  showPopup(params: {
    title?: string
    message: string
    buttons?: Array<{ id?: string; type?: string; text?: string }>
  }, callback?: (buttonId: string) => void): void
  setHeaderColor(color: string): void
  setBackgroundColor(color: string): void
  enableClosingConfirmation(): void
  disableClosingConfirmation(): void
  onEvent(eventType: string, eventHandler: () => void): void
  offEvent(eventType: string, eventHandler: () => void): void
}

declare global {
  interface Window {
    Telegram?: {
      WebApp: TelegramWebApp
    }
  }
}

export const twa = window.Telegram?.WebApp

export function isTelegramWebApp(): boolean {
  return Boolean(twa?.initData)
}

export function getTelegramUser() {
  return twa?.initDataUnsafe?.user ?? null
}

export function getInitData(): string {
  return twa?.initData ?? ''
}

export function hapticImpact(style: 'light' | 'medium' | 'heavy' = 'light') {
  twa?.HapticFeedback?.impactOccurred(style)
}

export function hapticSuccess() {
  twa?.HapticFeedback?.notificationOccurred('success')
}

export function hapticError() {
  twa?.HapticFeedback?.notificationOccurred('error')
}

export function hapticWarning() {
  twa?.HapticFeedback?.notificationOccurred('warning')
}

export function openLink(url: string) {
  if (twa) {
    twa.openLink(url)
  } else {
    window.open(url, '_blank')
  }
}

export function openInvoice(
  url: string,
  callback?: (status: 'paid' | 'cancelled' | 'failed' | 'pending') => void,
) {
  twa?.openInvoice(url, callback)
}

export function shareUrl(url: string, text?: string) {
  const shareText = text ? `${text}\n${url}` : url
  twa?.openTelegramLink(`https://t.me/share/url?url=${encodeURIComponent(url)}&text=${encodeURIComponent(text ?? '')}`)
}
