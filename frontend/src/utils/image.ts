/** 需要代理的图片域名（防盗链/跨域）；本地路径直接返回 */
const PROXY_HOSTS = ['patchwiki.biligame.com', 'hdslb.com']

export function getImageSrc(url: string | undefined): string {
  if (!url) return ''
  // 已是本地路径（如 /api/images/xxx），直接使用，不经过代理
  if (url.startsWith('/')) return url
  try {
    const host = new URL(url).hostname
    if (PROXY_HOSTS.some((h) => host.includes(h))) {
      return `/api/image-proxy?url=${encodeURIComponent(url)}`
    }
  } catch {
    // invalid url
  }
  return url
}
