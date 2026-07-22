export function formatDateTime(timestamp) {
  if (!timestamp) return '-'
  const date = new Date(timestamp)
  const pad = (n) => n.toString().padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
}

export function formatBytes(bytes) {
  if (!bytes || bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

export function formatStatus(status) {
  const statusMap = {
    active: { label: '活跃', type: 'success' },
    offline: { label: '离线', type: 'info' },
    pending: { label: '待执行', type: 'warning' },
    executing: { label: '执行中', type: 'primary' },
    completed: { label: '已完成', type: 'success' },
    failed: { label: '失败', type: 'danger' },
    'in-transit': { label: '传输中', type: 'primary' },
    exfiltrated: { label: '已窃取', type: 'success' },
    blocked: { label: '已拦截', type: 'danger' }
  }
  return statusMap[status] || { label: status, type: 'default' }
}

export function getWalletTypeName(walletType) {
  const walletTypes = {
    metamask: 'MetaMask',
    trust: 'Trust Wallet',
    coinbase: 'Coinbase Wallet',
    imtoken: 'imToken',
    tokenpocket: 'TokenPocket',
    alphawallet: 'AlphaWallet',
    mathwallet: 'MathWallet',
    tronlink: 'TronLink',
    onto: 'ONTO',
    bitpie: 'Bitpie',
    huobi: 'Huobi Wallet',
    phantom: 'Phantom',
    keplr: 'Keplr',
    cosmostation: 'Cosmostation'
  }
  return walletTypes[walletType] || walletType
}

export function getCategoryName(category) {
  const categories = {
    'keychain': 'Keychain',
    'wifi': 'WiFi',
    'photos': '照片',
    'contacts': '通讯录',
    'sms': '短信',
    'calls': '通话',
    'files': '文件',
    'wallet': '钱包'
  }
  return categories[category] || category
}

export function getCategoryType(category) {
  const types = {
    'keychain': 'danger',
    'wifi': 'warning',
    'photos': 'success',
    'contacts': 'primary',
    'sms': 'info',
    'calls': 'info',
    'files': 'info',
    'wallet': 'warning'
  }
  return types[category] || 'info'
}

export function truncateText(text, maxLength = 50) {
  if (!text) return '-'
  if (text.length <= maxLength) return text
  return text.slice(0, maxLength) + '...'
}