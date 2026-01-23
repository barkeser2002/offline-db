"use client";

import { motion } from "framer-motion";
import { Card, CardBody, Progress } from "@nextui-org/react";
import { Line } from "react-chartjs-2";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from "chart.js";

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
);

const stats = [
  { label: "Total Users", value: "12,345", change: "+12%", trend: "up" },
  { label: "Total Anime", value: "1,250", change: "+5%", trend: "up" },
  { label: "Active Streams", value: "453", change: "+24%", trend: "up" },
  { label: "Storage Used", value: "4.2 TB", change: "85%", trend: "warning" },
];

const chartData = {
  labels: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul"],
  datasets: [
    {
      label: "New Users",
      data: [65, 59, 80, 81, 56, 120, 150],
      fill: true,
      borderColor: "rgb(125, 42, 232)",
      backgroundColor: "rgba(125, 42, 232, 0.2)",
      tension: 0.4,
    },
    {
      label: "Active Streams",
      data: [28, 48, 40, 79, 86, 100, 140],
      fill: true,
      borderColor: "rgb(16, 185, 129)",
      backgroundColor: "rgba(16, 185, 129, 0.2)",
      tension: 0.4,
    },
  ],
};

const chartOptions = {
  responsive: true,
  plugins: {
    legend: {
      position: "top" as const,
      labels: { color: "rgba(255, 255, 255, 0.7)" },
    },
  },
  scales: {
    y: {
      grid: { color: "rgba(255, 255, 255, 0.1)" },
      ticks: { color: "rgba(255, 255, 255, 0.5)" },
    },
    x: {
      grid: { color: "rgba(255, 255, 255, 0.1)" },
      ticks: { color: "rgba(255, 255, 255, 0.5)" },
    },
  },
};

export default function AdminOverview() {
  return (
    <div className="space-y-6">
      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, index) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
          >
            <Card className="bg-surface border border-white/5">
              <CardBody className="p-6">
                <p className="text-foreground/60 text-sm mb-2">{stat.label}</p>
                <div className="flex items-end justify-between">
                  <h3 className="text-2xl font-bold text-foreground">
                    {stat.value}
                  </h3>
                  <span
                    className={`text-sm font-medium ${
                      stat.trend === "up"
                        ? "text-success"
                        : stat.trend === "down"
                          ? "text-danger"
                          : "text-warning"
                    }`}
                  >
                    {stat.change}
                  </span>
                </div>
              </CardBody>
            </Card>
          </motion.div>
        ))}
      </div>

      {/* Main Chart */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
      >
        <Card className="bg-surface border border-white/5">
          <CardBody className="p-6">
            <h3 className="text-lg font-semibold text-foreground mb-6">
              Traffic Overview
            </h3>
            <div className="h-[400px]">
              <Line data={chartData} options={chartOptions} />
            </div>
          </CardBody>
        </Card>
      </motion.div>

      {/* System Status */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="bg-surface border border-white/5">
          <CardBody className="p-6">
            <h3 className="text-lg font-semibold text-foreground mb-4">
              System Health
            </h3>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-foreground/70">CPU Usage</span>
                  <span className="text-primary font-medium">45%</span>
                </div>
                <Progress value={45} color="primary" size="sm" />
              </div>
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-foreground/70">Memory Usage</span>
                  <span className="text-warning font-medium">62%</span>
                </div>
                <Progress value={62} color="warning" size="sm" />
              </div>
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-foreground/70">Disk Space (S3)</span>
                  <span className="text-success font-medium">2.1TB / 5TB</span>
                </div>
                <Progress value={42} color="success" size="sm" />
              </div>
            </div>
          </CardBody>
        </Card>

        <Card className="bg-surface border border-white/5">
          <CardBody className="p-6">
            <h3 className="text-lg font-semibold text-foreground mb-4">
              Recent Transcodes
            </h3>
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <div
                  key={i}
                  className="flex items-center justify-between p-3 bg-white/5 rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-2 h-2 rounded-full bg-success animate-pulse" />
                    <div>
                      <p className="text-sm font-medium text-foreground">
                        Episode_{100 + i}.mkv
                      </p>
                      <p className="text-xs text-foreground/50">
                        Processing 1080p...
                      </p>
                    </div>
                  </div>
                  <span className="text-xs font-mono text-primary">78%</span>
                </div>
              ))}
            </div>
          </CardBody>
        </Card>
      </div>
    </div>
  );
}
