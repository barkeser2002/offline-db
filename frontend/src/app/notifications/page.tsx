"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Card, CardBody, Button, Chip, Switch } from "@nextui-org/react";
import Link from "next/link";

// Sample notifications
const notifications = [
  {
    id: 1,
    type: "episode",
    title: "New Episode Available",
    message: "Sousou no Frieren Episode 15 is now available",
    time: "5 min ago",
    read: false,
    link: "/watch/52991/15",
  },
  {
    id: 2,
    type: "episode",
    title: "New Episode Available",
    message: "One Punch Man S3 Episode 8 is now available",
    time: "1 hour ago",
    read: false,
    link: "/watch/21/8",
  },
  {
    id: 3,
    type: "system",
    title: "Welcome to AniScrap!",
    message: "Thanks for joining. Start exploring anime now!",
    time: "1 day ago",
    read: true,
    link: "/discovery",
  },
  {
    id: 4,
    type: "social",
    title: "New Follower",
    message: "anime_fan started following you",
    time: "2 days ago",
    read: true,
    link: "/profile",
  },
];

export default function NotificationsPage() {
  const [notifs, setNotifs] = useState(notifications);
  const [showUnreadOnly, setShowUnreadOnly] = useState(false);

  const filteredNotifs = showUnreadOnly
    ? notifs.filter((n) => !n.read)
    : notifs;
  const unreadCount = notifs.filter((n) => !n.read).length;

  const markAllRead = () => {
    setNotifs(notifs.map((n) => ({ ...n, read: true })));
  };

  const markAsRead = (id: number) => {
    setNotifs(notifs.map((n) => (n.id === id ? { ...n, read: true } : n)));
  };

  const getIcon = (type: string) => {
    switch (type) {
      case "episode":
        return (
          <svg
            className="w-5 h-5 text-primary"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z"
              clipRule="evenodd"
            />
          </svg>
        );
      case "system":
        return (
          <svg
            className="w-5 h-5 text-secondary"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
        );
      case "social":
        return (
          <svg
            className="w-5 h-5 text-accent"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
            />
          </svg>
        );
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen py-8">
      <div className="max-w-3xl mx-auto px-4">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center justify-between mb-8"
        >
          <div>
            <h1 className="text-3xl font-bold text-foreground mb-2">
              Notifications
            </h1>
            <p className="text-foreground/60">
              {unreadCount > 0
                ? `You have ${unreadCount} unread notifications`
                : "All caught up!"}
            </p>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <span className="text-sm text-foreground/60">Unread only</span>
              <Switch
                size="sm"
                isSelected={showUnreadOnly}
                onValueChange={setShowUnreadOnly}
                color="primary"
              />
            </div>
            <Button
              size="sm"
              variant="bordered"
              onClick={markAllRead}
              isDisabled={unreadCount === 0}
            >
              Mark all read
            </Button>
          </div>
        </motion.div>

        {/* Notifications List */}
        <div className="space-y-3">
          {filteredNotifs.map((notif, index) => (
            <motion.div
              key={notif.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.05 }}
            >
              <Link href={notif.link} onClick={() => markAsRead(notif.id)}>
                <Card
                  className={`border transition-all group ${
                    notif.read
                      ? "bg-surface/50 border-white/5 hover:border-white/10"
                      : "bg-surface border-primary/30 hover:border-primary/50"
                  }`}
                >
                  <CardBody className="p-4">
                    <div className="flex gap-4">
                      {/* Icon */}
                      <div
                        className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 ${
                          notif.read ? "bg-white/5" : "bg-primary/20"
                        }`}
                      >
                        {getIcon(notif.type)}
                      </div>

                      {/* Content */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <h3
                            className={`font-semibold group-hover:text-primary transition-colors ${
                              notif.read
                                ? "text-foreground/70"
                                : "text-foreground"
                            }`}
                          >
                            {notif.title}
                          </h3>
                          {!notif.read && (
                            <span className="w-2 h-2 rounded-full bg-primary" />
                          )}
                        </div>
                        <p className="text-sm text-foreground/60 mb-2">
                          {notif.message}
                        </p>
                        <span className="text-xs text-foreground/40">
                          {notif.time}
                        </span>
                      </div>

                      {/* Type Chip */}
                      <Chip
                        size="sm"
                        variant="flat"
                        color={
                          notif.type === "episode"
                            ? "primary"
                            : notif.type === "system"
                              ? "secondary"
                              : "warning"
                        }
                        className="flex-shrink-0"
                      >
                        {notif.type}
                      </Chip>
                    </div>
                  </CardBody>
                </Card>
              </Link>
            </motion.div>
          ))}
        </div>

        {/* Empty State */}
        {filteredNotifs.length === 0 && (
          <Card className="bg-surface border border-white/5">
            <CardBody className="p-12 text-center">
              <svg
                className="w-16 h-16 mx-auto text-foreground/20 mb-4"
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
              <h3 className="text-xl font-semibold text-foreground/70 mb-2">
                No notifications
              </h3>
              <p className="text-foreground/50">
                {showUnreadOnly
                  ? "No unread notifications"
                  : "You're all caught up!"}
              </p>
            </CardBody>
          </Card>
        )}

        {/* Notification Settings Link */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="mt-8 text-center"
        >
          <Button
            as={Link}
            href="/profile?tab=settings"
            variant="light"
            color="primary"
          >
            Notification Settings
          </Button>
        </motion.div>
      </div>
    </div>
  );
}
