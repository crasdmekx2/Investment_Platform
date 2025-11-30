import { Link, useLocation } from 'react-router-dom';

interface NavItem {
  path: string;
  label: string;
  icon?: React.ReactNode;
}

const navItems: NavItem[] = [
  { path: '/', label: 'Dashboard' },
  { path: '/portfolio', label: 'Portfolio' },
  { path: '/scheduler', label: 'Scheduler' },
];

export function Sidebar() {
  const location = useLocation();

  return (
    <aside className="w-64 bg-white border-r border-gray-200 min-h-screen">
      <div className="p-4">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Navigation</h2>
        <nav className="space-y-1">
          {navItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                location.pathname === item.path
                  ? 'bg-primary-100 text-primary-700'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              {item.icon && <span className="mr-3">{item.icon}</span>}
              {item.label}
            </Link>
          ))}
        </nav>
      </div>
    </aside>
  );
}

