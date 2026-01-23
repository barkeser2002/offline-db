"use client";

import { motion } from "framer-motion";
import { Card, CardBody } from "@nextui-org/react";

interface Stat {
  label: string;
  value: string | number;
}

const stats: Stat[] = [
  { label: "ANIMES", value: 3 },
  { label: "EPISODES", value: 56 },
  { label: "STREAMS", value: 0 },
];

export default function StatsSection() {
  return (
    <section className="py-8">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex flex-wrap justify-center gap-4">
          {stats.map((stat, index) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: index * 0.15 }}
              className="flex-1 min-w-[140px] max-w-[200px]"
            >
              <Card className="bg-surface/50 border border-white/10 hover:border-primary/30 transition-all">
                <CardBody className="text-center py-6">
                  <motion.span
                    className="text-3xl font-bold text-primary block"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: index * 0.15 + 0.3 }}
                  >
                    {stat.value}
                  </motion.span>
                  <span className="text-xs text-foreground/50 uppercase tracking-wider mt-1">
                    {stat.label}
                  </span>
                </CardBody>
              </Card>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
