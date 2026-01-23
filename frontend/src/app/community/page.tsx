"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import {
  Card,
  CardBody,
  Avatar,
  Button,
  Tabs,
  Tab,
  Textarea,
  Chip,
  Badge,
} from "@nextui-org/react";
import Link from "next/link";

// Sample community data
const activities = [
  {
    id: 1,
    user: "testuser",
    avatar: "",
    action: "started watching",
    target: "Sousou no Frieren",
    time: "2 min ago",
    type: "watch",
  },
  {
    id: 2,
    user: "anime_fan",
    avatar: "",
    action: "rated",
    target: "Cowboy Bebop",
    score: 9,
    time: "5 min ago",
    type: "rate",
  },
  {
    id: 3,
    user: "otaku_123",
    avatar: "",
    action: "added to list",
    target: "Attack on Titan",
    time: "12 min ago",
    type: "list",
  },
  {
    id: 4,
    user: "weeb_master",
    avatar: "",
    action: "completed",
    target: "Death Note",
    time: "18 min ago",
    type: "complete",
  },
  {
    id: 5,
    user: "shounen_lover",
    avatar: "",
    action: "started watching",
    target: "One Punch Man",
    time: "25 min ago",
    type: "watch",
  },
];

const topUsers = [
  { id: 1, username: "anime_master", avatar: "", watchedCount: 342, rank: 1 },
  { id: 2, username: "otaku_king", avatar: "", watchedCount: 289, rank: 2 },
  { id: 3, username: "weeb_queen", avatar: "", watchedCount: 256, rank: 3 },
  { id: 4, username: "shounen_fan", avatar: "", watchedCount: 234, rank: 4 },
  { id: 5, username: "slice_life", avatar: "", watchedCount: 198, rank: 5 },
];

const discussions = [
  {
    id: 1,
    title: "What's your favorite anime of 2024?",
    author: "anime_fan",
    replies: 42,
    views: 1250,
  },
  {
    id: 2,
    title: "Frieren ending discussion (SPOILERS)",
    author: "elf_lover",
    replies: 89,
    views: 3420,
  },
  {
    id: 3,
    title: "Best anime openings of all time?",
    author: "music_weeb",
    replies: 156,
    views: 5670,
  },
];

export default function CommunityPage() {
  const [selectedTab, setSelectedTab] = useState("activity");

  return (
    <div className="min-h-screen py-8">
      <div className="max-w-7xl mx-auto px-4">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="text-4xl font-bold text-foreground mb-2">
            <span className="gradient-text">Community</span> Hub
          </h1>
          <p className="text-foreground/60">
            Connect with fellow anime enthusiasts
          </p>
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2">
            <Tabs
              selectedKey={selectedTab}
              onSelectionChange={(key) => setSelectedTab(key as string)}
              variant="underlined"
              classNames={{
                tabList: "border-b border-white/10 pb-0",
                tab: "text-foreground/60 data-[selected=true]:text-primary font-medium py-4",
                cursor: "bg-primary",
              }}
            >
              <Tab key="activity" title="Activity Feed">
                <div className="space-y-4 mt-6">
                  {activities.map((activity, index) => (
                    <motion.div
                      key={activity.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.05 }}
                    >
                      <Card className="bg-surface border border-white/5 hover:border-white/10 transition-colors">
                        <CardBody className="p-4">
                          <div className="flex items-center gap-4">
                            <Avatar
                              name={activity.user}
                              size="md"
                              className="bg-primary/20 text-primary"
                            />
                            <div className="flex-1">
                              <p className="text-foreground">
                                <span className="font-semibold text-primary">
                                  {activity.user}
                                </span>{" "}
                                <span className="text-foreground/70">
                                  {activity.action}
                                </span>{" "}
                                <Link
                                  href="#"
                                  className="font-medium hover:text-primary"
                                >
                                  {activity.target}
                                </Link>
                                {activity.score && (
                                  <span className="ml-2 text-yellow-400 font-semibold">
                                    ★ {activity.score}/10
                                  </span>
                                )}
                              </p>
                              <p className="text-xs text-foreground/40 mt-1">
                                {activity.time}
                              </p>
                            </div>
                            <Chip
                              size="sm"
                              variant="flat"
                              color={
                                activity.type === "watch"
                                  ? "primary"
                                  : activity.type === "rate"
                                    ? "warning"
                                    : activity.type === "complete"
                                      ? "success"
                                      : "default"
                              }
                            >
                              {activity.type}
                            </Chip>
                          </div>
                        </CardBody>
                      </Card>
                    </motion.div>
                  ))}
                </div>
              </Tab>

              <Tab key="discussions" title="Discussions">
                <div className="space-y-4 mt-6">
                  {discussions.map((disc, index) => (
                    <motion.div
                      key={disc.id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.05 }}
                    >
                      <Card className="bg-surface border border-white/5 hover:border-primary/30 transition-colors cursor-pointer group">
                        <CardBody className="p-4">
                          <h3 className="font-semibold text-foreground group-hover:text-primary transition-colors mb-2">
                            {disc.title}
                          </h3>
                          <div className="flex items-center gap-4 text-sm text-foreground/50">
                            <span>
                              by{" "}
                              <span className="text-primary">
                                {disc.author}
                              </span>
                            </span>
                            <span>💬 {disc.replies} replies</span>
                            <span>👁 {disc.views} views</span>
                          </div>
                        </CardBody>
                      </Card>
                    </motion.div>
                  ))}

                  <Button
                    color="primary"
                    variant="bordered"
                    className="w-full mt-4"
                  >
                    Start New Discussion
                  </Button>
                </div>
              </Tab>
            </Tabs>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Top Users */}
            <Card className="bg-surface border border-white/5">
              <CardBody className="p-6">
                <h3 className="font-semibold text-foreground mb-4 flex items-center gap-2">
                  <span className="text-yellow-400">🏆</span> Top Watchers
                </h3>
                <div className="space-y-3">
                  {topUsers.map((user) => (
                    <div key={user.id} className="flex items-center gap-3">
                      <span
                        className={`w-6 text-center font-bold ${
                          user.rank === 1
                            ? "text-yellow-400"
                            : user.rank === 2
                              ? "text-gray-400"
                              : user.rank === 3
                                ? "text-amber-600"
                                : "text-foreground/50"
                        }`}
                      >
                        #{user.rank}
                      </span>
                      <Avatar
                        name={user.username}
                        size="sm"
                        className="bg-primary/20 text-primary"
                      />
                      <div className="flex-1">
                        <p className="text-sm font-medium text-foreground">
                          {user.username}
                        </p>
                        <p className="text-xs text-foreground/50">
                          {user.watchedCount} anime
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardBody>
            </Card>

            {/* Quick Stats */}
            <Card className="bg-surface border border-white/5">
              <CardBody className="p-6">
                <h3 className="font-semibold text-foreground mb-4">
                  Community Stats
                </h3>
                <div className="grid grid-cols-2 gap-4 text-center">
                  <div>
                    <p className="text-2xl font-bold text-primary">1,234</p>
                    <p className="text-xs text-foreground/50">Members</p>
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-accent">5,678</p>
                    <p className="text-xs text-foreground/50">Reviews</p>
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-secondary">123</p>
                    <p className="text-xs text-foreground/50">Discussions</p>
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-success">89</p>
                    <p className="text-xs text-foreground/50">Online Now</p>
                  </div>
                </div>
              </CardBody>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
