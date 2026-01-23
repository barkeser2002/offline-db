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
  Chip,
  Progress,
  Input,
} from "@nextui-org/react";
import Link from "next/link";

// Sample user data
const userData = {
  username: "anime_lover",
  email: "user@example.com",
  avatar: "",
  joinDate: "January 2024",
  bio: "Just a person who loves anime 🎌",
  stats: {
    watching: 5,
    completed: 42,
    planToWatch: 128,
    onHold: 8,
    dropped: 3,
    totalEpisodes: 1250,
  },
  recentActivity: [
    { anime: "Sousou no Frieren", episode: 15, date: "Today" },
    { anime: "Cowboy Bebop", episode: 26, date: "Yesterday" },
    { anime: "One Punch Man", episode: 8, date: "2 days ago" },
  ],
  favorites: [
    { id: 1, title: "Steins;Gate", score: 10 },
    { id: 2, title: "Death Note", score: 9 },
    { id: 3, title: "Attack on Titan", score: 9 },
  ],
};

export default function ProfilePage() {
  const [selectedTab, setSelectedTab] = useState("overview");
  const [isEditing, setIsEditing] = useState(false);
  const [bio, setBio] = useState(userData.bio);

  const totalAnime = Object.values(userData.stats)
    .slice(0, 5)
    .reduce((a, b) => a + b, 0);

  return (
    <div className="min-h-screen py-8">
      <div className="max-w-6xl mx-auto px-4">
        {/* Profile Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <Card className="bg-gradient-to-r from-primary/20 to-accent/20 border border-white/10">
            <CardBody className="p-6 md:p-8">
              <div className="flex flex-col md:flex-row items-center gap-6">
                <Avatar
                  name={userData.username}
                  className="w-24 h-24 text-3xl bg-primary"
                />
                <div className="text-center md:text-left flex-1">
                  <h1 className="text-2xl font-bold text-foreground mb-1">
                    {userData.username}
                  </h1>
                  <p className="text-foreground/60 mb-2">{userData.email}</p>
                  {isEditing ? (
                    <div className="flex gap-2 max-w-md">
                      <Input
                        size="sm"
                        value={bio}
                        onChange={(e) => setBio(e.target.value)}
                        classNames={{ inputWrapper: "bg-background/50" }}
                      />
                      <Button
                        size="sm"
                        color="primary"
                        onClick={() => setIsEditing(false)}
                      >
                        Save
                      </Button>
                    </div>
                  ) : (
                    <p className="text-foreground/70 mb-2">{bio}</p>
                  )}
                  <p className="text-sm text-foreground/50">
                    Member since {userData.joinDate}
                  </p>
                </div>
                <Button
                  color="primary"
                  variant="bordered"
                  onClick={() => setIsEditing(!isEditing)}
                >
                  {isEditing ? "Cancel" : "Edit Profile"}
                </Button>
              </div>
            </CardBody>
          </Card>
        </motion.div>

        {/* Stats Overview */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8"
        >
          <Card className="bg-primary/20 border border-primary/30">
            <CardBody className="p-4 text-center">
              <p className="text-2xl font-bold text-primary">
                {userData.stats.watching}
              </p>
              <p className="text-xs text-foreground/60">Watching</p>
            </CardBody>
          </Card>
          <Card className="bg-success/20 border border-success/30">
            <CardBody className="p-4 text-center">
              <p className="text-2xl font-bold text-success">
                {userData.stats.completed}
              </p>
              <p className="text-xs text-foreground/60">Completed</p>
            </CardBody>
          </Card>
          <Card className="bg-warning/20 border border-warning/30">
            <CardBody className="p-4 text-center">
              <p className="text-2xl font-bold text-warning">
                {userData.stats.planToWatch}
              </p>
              <p className="text-xs text-foreground/60">Plan to Watch</p>
            </CardBody>
          </Card>
          <Card className="bg-secondary/20 border border-secondary/30">
            <CardBody className="p-4 text-center">
              <p className="text-2xl font-bold text-secondary">
                {userData.stats.onHold}
              </p>
              <p className="text-xs text-foreground/60">On Hold</p>
            </CardBody>
          </Card>
          <Card className="bg-danger/20 border border-danger/30">
            <CardBody className="p-4 text-center">
              <p className="text-2xl font-bold text-danger">
                {userData.stats.dropped}
              </p>
              <p className="text-xs text-foreground/60">Dropped</p>
            </CardBody>
          </Card>
        </motion.div>

        {/* Tabs */}
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
          <Tab key="overview" title="Overview">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
              {/* Stats Chart */}
              <Card className="bg-surface border border-white/5">
                <CardBody className="p-6">
                  <h3 className="font-semibold text-foreground mb-4">
                    Anime Distribution
                  </h3>
                  <div className="space-y-3">
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-foreground/70">Watching</span>
                        <span className="text-primary">
                          {userData.stats.watching}
                        </span>
                      </div>
                      <Progress
                        value={(userData.stats.watching / totalAnime) * 100}
                        color="primary"
                        size="sm"
                      />
                    </div>
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-foreground/70">Completed</span>
                        <span className="text-success">
                          {userData.stats.completed}
                        </span>
                      </div>
                      <Progress
                        value={(userData.stats.completed / totalAnime) * 100}
                        color="success"
                        size="sm"
                      />
                    </div>
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-foreground/70">
                          Plan to Watch
                        </span>
                        <span className="text-warning">
                          {userData.stats.planToWatch}
                        </span>
                      </div>
                      <Progress
                        value={(userData.stats.planToWatch / totalAnime) * 100}
                        color="warning"
                        size="sm"
                      />
                    </div>
                  </div>
                  <div className="mt-4 pt-4 border-t border-white/10">
                    <p className="text-sm text-foreground/60">
                      Total episodes watched:{" "}
                      <span className="text-primary font-semibold">
                        {userData.stats.totalEpisodes}
                      </span>
                    </p>
                  </div>
                </CardBody>
              </Card>

              {/* Recent Activity */}
              <Card className="bg-surface border border-white/5">
                <CardBody className="p-6">
                  <h3 className="font-semibold text-foreground mb-4">
                    Recent Activity
                  </h3>
                  <div className="space-y-3">
                    {userData.recentActivity.map((activity, index) => (
                      <div
                        key={index}
                        className="flex items-center gap-3 p-2 rounded-lg hover:bg-white/5"
                      >
                        <div className="w-10 h-10 rounded bg-primary/20 flex items-center justify-center">
                          <span className="text-primary text-xs font-bold">
                            E{activity.episode}
                          </span>
                        </div>
                        <div className="flex-1">
                          <p className="text-sm font-medium text-foreground">
                            {activity.anime}
                          </p>
                          <p className="text-xs text-foreground/50">
                            Episode {activity.episode}
                          </p>
                        </div>
                        <span className="text-xs text-foreground/40">
                          {activity.date}
                        </span>
                      </div>
                    ))}
                  </div>
                </CardBody>
              </Card>
            </div>
          </Tab>

          <Tab key="favorites" title="Favorites">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
              {userData.favorites.map((anime, index) => (
                <motion.div
                  key={anime.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                >
                  <Card className="bg-surface border border-white/5 hover:border-primary/30 transition-colors">
                    <CardBody className="p-0">
                      <div className="aspect-[2/3] bg-surface-light flex items-center justify-center text-2xl text-primary/30">
                        {anime.title.charAt(0)}
                      </div>
                      <div className="p-3">
                        <h4 className="font-medium text-sm text-foreground truncate">
                          {anime.title}
                        </h4>
                        <div className="flex items-center gap-1 mt-1">
                          <span className="text-yellow-400 text-xs">★</span>
                          <span className="text-xs text-foreground/60">
                            {anime.score}/10
                          </span>
                        </div>
                      </div>
                    </CardBody>
                  </Card>
                </motion.div>
              ))}
              <Card className="bg-surface/50 border border-dashed border-white/20 hover:border-primary/50 transition-colors cursor-pointer">
                <CardBody className="flex items-center justify-center aspect-[2/3]">
                  <div className="text-center">
                    <span className="text-3xl text-foreground/20">+</span>
                    <p className="text-xs text-foreground/40 mt-2">
                      Add Favorite
                    </p>
                  </div>
                </CardBody>
              </Card>
            </div>
          </Tab>

          <Tab key="settings" title="Settings">
            <div className="mt-6 max-w-xl">
              <Card className="bg-surface border border-white/5">
                <CardBody className="p-6 space-y-4">
                  <Input
                    label="Username"
                    value={userData.username}
                    variant="bordered"
                    classNames={{
                      inputWrapper: "bg-background/50 border-white/10",
                    }}
                  />
                  <Input
                    label="Email"
                    type="email"
                    value={userData.email}
                    variant="bordered"
                    classNames={{
                      inputWrapper: "bg-background/50 border-white/10",
                    }}
                  />
                  <Input
                    label="Current Password"
                    type="password"
                    placeholder="••••••••"
                    variant="bordered"
                    classNames={{
                      inputWrapper: "bg-background/50 border-white/10",
                    }}
                  />
                  <Input
                    label="New Password"
                    type="password"
                    placeholder="••••••••"
                    variant="bordered"
                    classNames={{
                      inputWrapper: "bg-background/50 border-white/10",
                    }}
                  />
                  <div className="flex gap-4 pt-4">
                    <Button color="primary">Save Changes</Button>
                    <Button color="danger" variant="bordered">
                      Delete Account
                    </Button>
                  </div>
                </CardBody>
              </Card>
            </div>
          </Tab>
        </Tabs>
      </div>
    </div>
  );
}
