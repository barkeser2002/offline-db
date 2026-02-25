"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Navbar as NextUINavbar,
  NavbarBrand,
  NavbarContent,
  NavbarItem,
  NavbarMenuToggle,
  NavbarMenu,
  NavbarMenuItem,
  Button,
  Input,
  Badge,
  Dropdown,
  DropdownTrigger,
  DropdownMenu,
  DropdownItem,
  Avatar,
} from "@nextui-org/react";
import { motion } from "framer-motion";

const navItems = [
  { label: "Discovery", href: "/discovery", icon: "🔍" },
  { label: "Schedule", href: "/schedule", icon: "📅" },
  { label: "Community", href: "/community", icon: "👥" },
  { label: "Collections", href: "/collections", icon: "📚" },
];

export default function Navbar() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const pathname = usePathname();

  return (
    <NextUINavbar
      isMenuOpen={isMenuOpen}
      onMenuOpenChange={setIsMenuOpen}
      classNames={{
        base: "bg-background/80 backdrop-blur-lg border-b border-white/10",
        wrapper: "max-w-7xl",
      }}
      isBordered
    >
      {/* Logo */}
      <NavbarContent>
        <NavbarMenuToggle
          aria-label={isMenuOpen ? "Close menu" : "Open menu"}
          className="sm:hidden text-foreground"
        />
        <NavbarBrand>
          <Link href="/" className="flex items-center gap-2">
            <div className="relative w-8 h-8">
              <img
                src="/aniscrap.svg"
                alt="AniScrap Logo"
                className="w-full h-full object-contain"
              />
            </div>
            <span className="font-bold text-xl text-foreground">AniScrap</span>
          </Link>
        </NavbarBrand>
      </NavbarContent>

      {/* Nav Links */}
      <NavbarContent className="hidden sm:flex gap-6" justify="center">
        {navItems.map((item) => (
          <NavbarItem key={item.href}>
            <Link
              href={item.href}
              className={`flex items-center gap-2 text-sm font-medium transition-colors ${
                pathname === item.href
                  ? "text-primary"
                  : "text-foreground/70 hover:text-foreground"
              }`}
            >
              <span>{item.icon}</span>
              {item.label}
            </Link>
          </NavbarItem>
        ))}
      </NavbarContent>

      {/* Right Side - Search + User */}
      <NavbarContent justify="end" className="gap-4">
        {/* Search */}
        <NavbarItem className="hidden md:flex">
          <Input
            classNames={{
              base: "max-w-[220px]",
              input: "text-sm",
              inputWrapper:
                "bg-surface border-white/10 hover:border-primary/50",
            }}
            placeholder="Search anime..."
            size="sm"
            aria-label="Search anime"
            startContent={
              <svg
                className="w-4 h-4 text-foreground/50"
                aria-hidden="true"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
              </svg>
            }
            type="search"
          />
        </NavbarItem>

        {/* Notifications */}
        <NavbarItem>
          <Badge content="3" color="danger" size="sm" placement="top-right">
            <Button
              isIconOnly
              variant="light"
              aria-label="Notifications"
              className="text-foreground/70 hover:text-foreground"
            >
              <svg
                className="w-5 h-5"
                aria-hidden="true"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
                />
              </svg>
            </Button>
          </Badge>
        </NavbarItem>

        {/* Login / User */}
        <NavbarItem>
          <Button
            as={Link}
            href="/login"
            color="primary"
            variant="shadow"
            size="sm"
            className="font-semibold"
          >
            Get Started
          </Button>
        </NavbarItem>
      </NavbarContent>

      {/* Mobile Menu */}
      <NavbarMenu className="bg-background/95 backdrop-blur-lg pt-6">
        {/* Mobile Search */}
        <div className="mb-4">
          <Input
            classNames={{
              inputWrapper: "bg-surface border-white/10",
            }}
            placeholder="Search anime..."
            size="lg"
            aria-label="Search anime"
            startContent={
              <svg
                className="w-5 h-5 text-foreground/50"
                aria-hidden="true"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
              </svg>
            }
            type="search"
          />
        </div>

        {navItems.map((item, index) => (
          <NavbarMenuItem key={item.href}>
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <Link
                href={item.href}
                className={`w-full flex items-center gap-3 py-3 text-lg ${
                  pathname === item.href
                    ? "text-primary font-semibold"
                    : "text-foreground/70"
                }`}
                onClick={() => setIsMenuOpen(false)}
              >
                <span className="text-xl">{item.icon}</span>
                {item.label}
              </Link>
            </motion.div>
          </NavbarMenuItem>
        ))}
      </NavbarMenu>
    </NextUINavbar>
  );
}
