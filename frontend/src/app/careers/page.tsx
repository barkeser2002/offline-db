"use client";

import { motion } from "framer-motion";
import { Card, CardBody, Button, Chip } from "@nextui-org/react";

const jobs = [
  {
    id: 1,
    title: "Senior Full-Stack Developer",
    department: "Engineering",
    location: "Remote",
    type: "Full-time",
    description:
      "Build and maintain our streaming platform using Next.js and Django",
  },
  {
    id: 2,
    title: "UI/UX Designer",
    department: "Design",
    location: "Remote",
    type: "Full-time",
    description:
      "Create beautiful, intuitive interfaces for our anime platform",
  },
  {
    id: 3,
    title: "Content Moderator",
    department: "Operations",
    location: "Remote",
    type: "Part-time",
    description:
      "Ensure community guidelines are followed and content quality is maintained",
  },
  {
    id: 4,
    title: "DevOps Engineer",
    department: "Engineering",
    location: "Remote",
    type: "Full-time",
    description: "Manage our infrastructure and ensure 99.9% uptime",
  },
];

const benefits = [
  "🏠 100% Remote Work",
  "💰 Competitive Salary",
  "🎮 Gaming & Anime Budget",
  "📚 Learning Stipend",
  "🏥 Health Insurance",
  "🌴 Unlimited PTO",
];

export default function CareersPage() {
  return (
    <div className="min-h-screen py-12">
      <div className="max-w-5xl mx-auto px-4">
        {/* Hero */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-12"
        >
          <h1 className="text-4xl font-bold text-foreground mb-4">
            Join the <span className="gradient-text">AniScrap</span> Team
          </h1>
          <p className="text-xl text-foreground/60 max-w-2xl mx-auto">
            Help us build the future of anime streaming
          </p>
        </motion.div>

        {/* Benefits */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="mb-12"
        >
          <Card className="bg-gradient-to-r from-primary/20 to-accent/20 border border-white/10">
            <CardBody className="p-8">
              <h2 className="text-xl font-semibold text-foreground mb-4 text-center">
                Why Work With Us?
              </h2>
              <div className="flex flex-wrap justify-center gap-4">
                {benefits.map((benefit, index) => (
                  <Chip
                    key={index}
                    size="lg"
                    variant="flat"
                    className="bg-white/10"
                  >
                    {benefit}
                  </Chip>
                ))}
              </div>
            </CardBody>
          </Card>
        </motion.div>

        {/* Open Positions */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <h2 className="text-2xl font-bold text-foreground mb-6">
            Open Positions
          </h2>
          <div className="space-y-4">
            {jobs.map((job, index) => (
              <motion.div
                key={job.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.3 + index * 0.1 }}
              >
                <Card className="bg-surface border border-white/5 hover:border-primary/30 transition-all cursor-pointer group">
                  <CardBody className="p-6">
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                      <div>
                        <h3 className="text-lg font-semibold text-foreground group-hover:text-primary transition-colors">
                          {job.title}
                        </h3>
                        <p className="text-foreground/60 text-sm mt-1">
                          {job.description}
                        </p>
                        <div className="flex flex-wrap gap-2 mt-3">
                          <Chip size="sm" color="primary" variant="flat">
                            {job.department}
                          </Chip>
                          <Chip size="sm" variant="bordered">
                            {job.location}
                          </Chip>
                          <Chip size="sm" variant="bordered">
                            {job.type}
                          </Chip>
                        </div>
                      </div>
                      <Button color="primary" className="flex-shrink-0">
                        Apply Now
                      </Button>
                    </div>
                  </CardBody>
                </Card>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* No positions */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="mt-12 text-center"
        >
          <Card className="bg-surface border border-white/5">
            <CardBody className="p-8">
              <p className="text-foreground/60 mb-4">
                Don't see a position that fits? We're always looking for
                talented people.
              </p>
              <Button color="primary" variant="bordered">
                Send Open Application
              </Button>
            </CardBody>
          </Card>
        </motion.div>
      </div>
    </div>
  );
}
