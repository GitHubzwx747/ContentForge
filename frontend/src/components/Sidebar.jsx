import { NavLink } from 'react-router-dom'
import { LayoutDashboard, PenLine, Clock, Settings2 } from 'lucide-react'

const navItems = [
  { to: '/', label: '数据概览', icon: LayoutDashboard },
  { to: '/generate', label: '生成文案', icon: PenLine },
  { to: '/history', label: '历史记录', icon: Clock },
  { to: '/models', label: '模型管理', icon: Settings2 },
]

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <h2>ContentForge</h2>
      </div>

      <nav className="sidebar-nav">
        {navItems.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `sidebar-link${isActive ? ' active' : ''}`
            }
          >
            <Icon size={18} />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}
