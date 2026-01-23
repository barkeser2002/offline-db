"use client";

import { motion } from "framer-motion";
import { Card, CardBody, Button, Avatar } from "@nextui-org/react";
import Link from "next/link";

const teamMembers = [
  { name: "Barış Keser", role: "Founder & Developer", avatar: "" },
];

const stats = [
  { label: "Anime Titles", value: "10,000+" },
  { label: "Episodes", value: "250,000+" },
  { label: "Active Users", value: "50,000+" },
  { label: "Countries", value: "120+" },
];

const features = [
  {
    icon: "🎬",
    title: "High Quality Streaming",
    description: "Watch anime in 1080p with adaptive bitrate",
  },
  {
    icon: "🔔",
    title: "Episode Notifications",
    description: "Get notified when new episodes air",
  },
  {
    icon: "📚",
    title: "Comprehensive Database",
    description: "Detailed info powered by MAL integration",
  },
  {
    icon: "👥",
    title: "Active Community",
    description: "Discuss and share with fellow fans",
  },
];

export default function AboutPage() {
  return (
    <div className="min-h-screen py-12">
      <div className="max-w-6xl mx-auto px-4">
        {/* Hero */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-16"
        >
          <h1 className="text-5xl font-bold text-foreground mb-4">
            About <span className="gradient-text">AniScrap</span>
          </h1>
          <p className="text-xl text-foreground/60 max-w-2xl mx-auto">
            Your next-generation anime streaming platform. Discover new worlds,
            track your progress, and join a passionate community.
          </p>
        </motion.div>

        {/* Stats */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-16"
        >
          {stats.map((stat, index) => (
            <Card key={index} className="bg-surface border border-white/5">
              <CardBody className="p-6 text-center">
                <p className="text-3xl font-bold gradient-text">{stat.value}</p>
                <p className="text-foreground/60 text-sm mt-1">{stat.label}</p>
              </CardBody>
            </Card>
          ))}
        </motion.div>

        {/* Mission */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="mb-16"
        >
          <Card className="bg-gradient-to-br from-primary/20 to-accent/20 border border-white/10">
            <CardBody className="p-8 md:p-12 text-center">
              <h2 className="text-2xl font-bold text-foreground mb-4">
                Our Mission
              </h2>
              <p className="text-foreground/80 text-lg max-w-3xl mx-auto">
                To create the ultimate anime experience by combining
                cutting-edge streaming technology with a passionate community.
                We believe everyone should have access to amazing anime content
                with the features they deserve.
              </p>
            </CardBody>
          </Card>
        </motion.div>

        {/* Features */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="mb-16"
        >
          <h2 className="text-2xl font-bold text-foreground text-center mb-8">
            What We Offer
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {features.map((feature, index) => (
              <Card
                key={index}
                className="bg-surface border border-white/5 hover:border-primary/30 transition-colors"
              >
                <CardBody className="p-6">
                  <div className="flex items-start gap-4">
                    <span className="text-3xl">{feature.icon}</span>
                    <div>
                      <h3 className="font-semibold text-foreground mb-1">
                        {feature.title}
                      </h3>
                      <p className="text-foreground/60 text-sm">
                        {feature.description}
                      </p>
                    </div>
                  </div>
                </CardBody>
              </Card>
            ))}
          </div>
        </motion.div>

        {/* Team */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="text-center mb-16"
        >
          <h2 className="text-2xl font-bold text-foreground mb-8">The Team</h2>
          <div className="flex justify-center gap-8">
            {teamMembers.map((member, index) => (
              <div key={index} className="text-center">
                <Avatar
                  name={member.name}
                  size="lg"
                  className="w-24 h-24 bg-primary text-xl mb-4"
                />
                <h3 className="font-semibold text-foreground">{member.name}</h3>
                <p className="text-foreground/60 text-sm">{member.role}</p>
              </div>
            ))}
          </div>
        </motion.div>

        {/* CTA */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="text-center"
        >
          <Card className="bg-surface border border-white/5">
            <CardBody className="p-8 md:p-12">
              <h2 className="text-2xl font-bold text-foreground mb-4">
                Ready to Start?
              </h2>
              <p className="text-foreground/60 mb-6">
                Join thousands of anime fans today
              </p>
              <div className="flex justify-center gap-4">
                <Button as={Link} href="/register" color="primary" size="lg">
                  Create Account
                </Button>
                <Button
                  as={Link}
                  href="/discovery"
                  variant="bordered"
                  size="lg"
                >
                  Browse Anime
                </Button>
              </div>
            </CardBody>
          </Card>
        </motion.div>
      </div>
    </div>
  );
}
