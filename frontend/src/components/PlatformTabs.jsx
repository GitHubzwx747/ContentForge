import { useState } from 'react'

const PLATFORM_LABELS = {
  xiaohongshu: '小红书',
  wechat: '微信公众号',
  douyin: '抖音',
}

export default function PlatformTabs({ platforms, children }) {
  const [active, setActive] = useState(platforms[0] || '')

  if (!platforms.length) return null

  return (
    <div>
      <div className="platform-tabs">
        {platforms.map((p) => (
          <button
            key={p}
            className={`platform-tab ${p === active ? 'platform-tab--active' : ''}`}
            onClick={() => setActive(p)}
          >
            {PLATFORM_LABELS[p] || p}
          </button>
        ))}
      </div>
      <div className="platform-tab-content" key={active}>
        {typeof children === 'function' ? children(active) : children}
      </div>
    </div>
  )
}
