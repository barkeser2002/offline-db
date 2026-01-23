"use client";

import { useState } from "react";
import { usePathname } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  Button,
  Avatar,
  Dropdown,
  DropdownTrigger,
  DropdownMenu,
  DropdownItem,
} from "@nextui-org/react";

const sidebarItems = [
  { label: "Overview", href: "/admin", icon: "📊" },
  { label: "Uploads", href: "/admin/upload", icon: "☁️" },
  { label: "Content", href: "/admin/content", icon: "🎬" },
  { label: "Users", href: "/admin/users", icon: "👥" },
  { label: "Settings", href: "/admin/settings", icon: "⚙️" },
];

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  return (
    <div className="min-h-screen bg-background flex">
      {/* Sidebar */}
      <motion.aside
        initial={{ width: 280 }}
        animate={{ width: isSidebarOpen ? 280 : 80 }}
        className="bg-surface border-r border-white/10 flex flex-col fixed h-full z-40"
      >
        <div className="p-6 flex items-center gap-3">
          <div className="w-8 h-8 relative flex-shrink-0">
            <img
              src="/aniscrap.svg"
              alt="Logo"
              className="w-full h-full object-contain"
            />
          </div>
          {isSidebarOpen && (
            <motion.span
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="font-bold text-xl text-foreground"
            >
              Admin Panel
            </motion.span>
          )}
        </div>

        <nav className="flex-1 px-4 space-y-2 mt-4">
          {sidebarItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-4 px-4 py-3 rounded-lg transition-colors ${
                pathname === item.href
                  ? "bg-primary/20 text-primary"
                  : "text-foreground/70 hover:bg-white/5 hover:text-foreground"
              }`}
            >
              <span className="text-xl">{item.icon}</span>
              {isSidebarOpen && (
                <motion.span
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="font-medium"
                >
                  {item.label}
                </motion.span>
              )}
            </Link>
          ))}
        </nav>

        <div className="p-4 border-t border-white/10">
          <button
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            className="w-full flex items-center justify-center p-2 text-foreground/50 hover:text-foreground transition-colors"
          >
            {isSidebarOpen ? "◀ Collapse" : "▶"}
          </button>
        </div>
      </motion.aside>

      {/* Main Content */}
      <main
        className={`flex-1 transition-all duration-300 ${isSidebarOpen ? "ml-[280px]" : "ml-[80px]"}`}
      >
        {/* Top Navbar */}
        <header className="h-16 bg-surface/50 backdrop-blur-lg border-b border-white/10 sticky top-0 z-30 px-8 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-foreground">
            {sidebarItems.find((i) => i.href === pathname)?.label ||
              "Dashboard"}
          </h2>

          <div className="flex items-center gap-4">
            <Dropdown>
              <DropdownTrigger>
                <div className="flex items-center gap-3 cursor-pointer">
                  <div className="text-right hidden sm:block">
                    <p className="text-sm font-medium text-foreground">
                      Admin User
                    </p>
                    <p className="text-xs text-foreground/50">Super Admin</p>
                  </div>
                  <Avatar name="Admin" className="bg-primary text-white" />
                </div>
              </DropdownTrigger>
              <DropdownMenu aria-label="Admin Profile">
                <DropdownItem key="profile">Profile</DropdownItem>
                <DropdownItem key="settings">Settings</DropdownItem>
                <DropdownItem
                  key="logout"
                  className="text-danger"
                  color="danger"
                >
                  Log Out
                </DropdownItem>
              </DropdownMenu>
            </Dropdown>
          </div>
        </header>

        <div className="p-8">{children}</div>
      </main>
    </div>
  );
}
