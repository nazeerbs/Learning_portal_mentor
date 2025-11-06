'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState, useEffect, useRef } from 'react';

export default function MentorLayout({ children }) {
  const pathname = usePathname();
  const [isProfileOpen, setProfileOpen] = useState(false);
  const [isSidebarCollapsed, setSidebarCollapsed] = useState(false);
  const profileDropdownRef = useRef(null);

  // Effect to handle clicking outside of the profile dropdown to close it
  useEffect(() => {
    function handleClickOutside(event) {
      if (profileDropdownRef.current && !profileDropdownRef.current.contains(event.target)) {
        setProfileOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [profileDropdownRef]);

  // Mock mentor data for display. In a real app, this would come from an auth context or API.
  const mentor = {
    name: 'Mentor',
  };

  // Mock notification counts. In a real app, this would come from an API.
  const notifications = {
    evaluations: 3,
    sessions: 1,
  };

  const navLinks = [
    {
      group: 'Workspace',
      items: [
        { href: '/mentor/dashboard_overview', label: 'Dashboard', icon: <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2H5a2 2 0 00-2-2z" /></svg> },
        { href: '/mentor/evaluations', label: 'Evaluations', notificationCount: notifications.evaluations, icon: <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" /></svg> },
        { href: '/mentor/interactions', label: 'Interactions', notificationCount: notifications.sessions, icon: <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg> },
      ]
    },
    {
      group: 'Management',
      items: [
        { href: '/mentor/courses', label: 'Courses', icon: <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" /></svg> },
        { href: '/mentor/studentprogress', label: 'Students', icon: <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" /></svg> },
        { href: '/mentor/Reports', label: 'Reports', icon: <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg> },
      ]
    },
  ];

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100">
      {/* Top Navbar - Fixed at top */}
      <nav className="fixed top-0 left-0 right-0 bg-gray-800 shadow-sm border-b border-gray-700 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-2">
          <div className="flex justify-between items-center h-16 gap-4">
            {/* Left section - Logo and Sidebar Toggle */}
            <div className="flex items-center">
              <button onClick={() => setSidebarCollapsed(!isSidebarCollapsed)} className="text-gray-400 hover:text-gray-200 p-1 rounded-md mr-4">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h7"/>
                </svg>
              </button>
              <div className="text-xl font-bold text-gray-100 flex items-center overflow-hidden">
                  <span className={`transition-all duration-300 ${isSidebarCollapsed ? 'ml-3' : ''}`}>G</span>
                  <span className={`whitespace-nowrap transition-opacity duration-200 ${isSidebarCollapsed ? 'opacity-0 w-0' : 'opacity-100'}`}>enAI99</span>
              </div>
            </div>

            {/* Center section (Search Bar) */}
            <div className="flex-1 flex justify-center px-2 lg:ml-6 lg:justify-start">
              <div className="w-full max-w-lg">
                <input
                  type="text"
                  placeholder="Search courses..."
                  className="w-full px-3 py-2 border border-gray-600 rounded-md bg-gray-700 text-gray-100 focus:outline-none focus:ring-2 focus:ring-gray-500"
                />
              </div>
            </div>

            {/* Right section */}
            <div className="flex items-center justify-end space-x-4">
              <span className="text-sm text-gray-300 hidden md:block">Hi, {mentor.name}!</span>
              <button className="p-2 text-gray-400 hover:text-gray-200 relative" onClick={() => alert('Notifications clicked!')}>
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 22c1.1 0 2-.9 2-2h-4c0 1.1.9 2 2 2zm6-6v-5c0-3.07-1.64-5.64-4.5-6.32V4c0-.83-.67-1.5-1.5-1.5s-1.5.67-1.5 1.5v.68C7.63 5.36 6 7.92 6 11v5l-2 2v1h16v-1l-2-2z" />
                </svg>
                {/* Notification dot */}
                <span className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full"></span>
              </button>
              <div className="relative" ref={profileDropdownRef}>
                <button
                  className="w-8 h-8 bg-gray-600 rounded-full flex items-center justify-center text-white font-semibold hover:bg-gray-500 transition-colors"
                  onClick={() => setProfileOpen(!isProfileOpen)}
                >
                  {mentor.name.charAt(0)}
                </button>
                {isProfileOpen && (
                  <div id="profile-dropdown" className="absolute right-0 mt-2 w-48 bg-gray-800 border border-gray-700 rounded-lg shadow-lg z-50">
                    <div className="py-1">
                      <Link href="#" className="block px-4 py-2 text-sm text-gray-300 hover:bg-gray-700 hover:text-gray-100">
                        Profile Settings
                      </Link>
                      <Link href="/mentor/help" className="block px-4 py-2 text-sm text-gray-300 hover:bg-gray-700 hover:text-gray-100">
                        Help & Support
                      </Link>
                      <Link href="#" className="block px-4 py-2 text-sm text-gray-300 hover:bg-gray-700 hover:text-gray-100">
                        Logout
                      </Link>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </nav>

      {/* Layout container for Sidebar and Main Content */}
      <div className="flex">
        {/* Collapsible Sidebar - Fixed on left (width reduced from w-64 to w-56) */}
        <aside className={`fixed left-0 top-16 bottom-0 bg-gray-800 shadow-sm border-r border-gray-700 z-30 overflow-x-hidden overflow-y-auto transition-all duration-300 ${isSidebarCollapsed ? 'w-20' : 'w-56'}`}>
            <nav className="mt-5 px-2 space-y-6">
              {navLinks.map((group) => (
                <div key={group.group}>
                  <h3 className={`px-2 mb-2 text-xs font-semibold text-gray-500 uppercase tracking-wider transition-opacity duration-200 ${isSidebarCollapsed ? 'opacity-0 h-0' : 'opacity-100'}`}>
                    {group.group}
                  </h3>
                  <div className="space-y-1">
                    {group.items.map(link => (
                      <Link
                        key={link.href}
                        href={link.href}
                        className={`group flex items-center p-2 text-base font-medium rounded-md transition-colors relative ${pathname.startsWith(link.href) ? 'bg-gray-700 text-gray-100' : 'text-gray-300 hover:bg-gray-700'}`}
                        title={isSidebarCollapsed ? link.label : ''}
                      >
                        <div className={`flex-shrink-0 transition-all duration-300 ${isSidebarCollapsed ? 'mx-auto' : 'mr-3'} ${isSidebarCollapsed && link.notificationCount > 0 ? 'text-red-400' : ''}`}>
                          {link.icon}
                        </div>
                        <span className={`whitespace-nowrap transition-opacity duration-200 ${isSidebarCollapsed ? 'opacity-0 w-0' : 'opacity-100'}`}>{link.label}</span>
                        {/* Show badge only when sidebar is not collapsed */}
                        {!isSidebarCollapsed && link.notificationCount > 0 && (
                          <span className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center justify-center px-2 h-5 text-xs font-bold text-white bg-red-500 rounded-full">
                            {link.notificationCount}
                          </span>
                        )}
                      </Link>
                    ))}
                  </div>
                </div>
              ))}
            </nav>
        </aside>

        {/* Main Content - Margin adjusted for new sidebar width */}
        <main className={`flex-1 pt-16 bg-gray-900 transition-all duration-300 ${isSidebarCollapsed ? 'ml-20' : 'ml-56'}`}>
          {children}
        </main>
      </div>
    </div>
  );
}