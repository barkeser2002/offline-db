"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import {
  Card,
  CardBody,
  Tabs,
  Tab,
  Input,
  Button,
  Progress,
  Select,
  SelectItem,
} from "@nextui-org/react";

export default function UploadPage() {
  const [selectedTab, setSelectedTab] = useState("direct");
  const [files, setFiles] = useState<File[]>([]);
  const [uploadProgress, setUploadProgress] = useState<Record<string, number>>(
    {},
  );

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files) {
      setFiles(Array.from(e.dataTransfer.files));
    }
  };

  const startUpload = () => {
    files.forEach((file) => {
      let progress = 0;
      const interval = setInterval(() => {
        progress += Math.random() * 10;
        if (progress >= 100) {
          progress = 100;
          clearInterval(interval);
        }
        setUploadProgress((prev) => ({ ...prev, [file.name]: progress }));
      }, 500);
    });
  };

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold text-foreground mb-6">
        Upload Content
      </h1>

      <Tabs
        selectedKey={selectedTab}
        onSelectionChange={(key) => setSelectedTab(key as string)}
        variant="underlined"
        classNames={{
          tabList: "border-b border-white/10 w-full",
          cursor: "bg-primary",
          tab: "h-12",
        }}
      >
        <Tab key="direct" title="Direct Upload">
          <div className="mt-6">
            <Card className="bg-surface border border-dashed border-white/20 hover:border-primary/50 transition-colors">
              <CardBody
                className="p-12 text-center cursor-pointer"
                onDragOver={handleDragOver}
                onDrop={handleDrop}
              >
                <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-4">
                  <svg
                    className="w-8 h-8 text-primary"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                    />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold text-foreground mb-2">
                  Drag & Drop Video Files
                </h3>
                <p className="text-foreground/50 mb-6">
                  or click to browse from your computer
                </p>
                <Button color="primary" variant="flat">
                  Select Files
                </Button>
              </CardBody>
            </Card>

            {/* Upload List */}
            {files.length > 0 && (
              <div className="mt-8 space-y-4">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="font-semibold text-foreground">
                    Upload Queue ({files.length})
                  </h3>
                  <Button size="sm" color="primary" onClick={startUpload}>
                    Start All
                  </Button>
                </div>
                {files.map((file, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                  >
                    <Card className="bg-surface border border-white/5">
                      <CardBody className="p-4">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-3">
                            <div className="w-8 h-8 rounded bg-white/10 flex items-center justify-center text-xs font-mono">
                              MKV
                            </div>
                            <div>
                              <p className="font-medium text-foreground text-sm">
                                {file.name}
                              </p>
                              <p className="text-xs text-foreground/50">
                                {(file.size / 1024 / 1024).toFixed(2)} MB
                              </p>
                            </div>
                          </div>
                          <span className="text-sm font-mono text-primary">
                            {uploadProgress[file.name]
                              ? `${Math.round(uploadProgress[file.name])}%`
                              : "Pending"}
                          </span>
                        </div>
                        <Progress
                          value={uploadProgress[file.name] || 0}
                          color="primary"
                          size="sm"
                          className="h-1"
                        />
                      </CardBody>
                    </Card>
                  </motion.div>
                ))}
              </div>
            )}
          </div>
        </Tab>

        <Tab key="magnet" title="Magnet Link">
          <div className="mt-6">
            <Card className="bg-surface border border-white/5">
              <CardBody className="p-6 space-y-4">
                <Input
                  label="Magnet Link / Torrent URL"
                  placeholder="magnet:?xt=urn:btih:..."
                  variant="bordered"
                  classNames={{
                    inputWrapper: "bg-background/50 border-white/10",
                  }}
                />
                <div className="flex gap-4">
                  <Select
                    label="Quality"
                    placeholder="Auto"
                    variant="bordered"
                    className="max-w-xs"
                  >
                    <SelectItem key="1080">1080p</SelectItem>
                    <SelectItem key="720">720p</SelectItem>
                    <SelectItem key="480">480p</SelectItem>
                  </Select>
                  <Button color="primary" size="lg" className="flex-1">
                    Start Download
                  </Button>
                </div>
              </CardBody>
            </Card>
          </div>
        </Tab>

        <Tab key="scrape" title="Scrape URL">
          <div className="mt-6">
            <Card className="bg-surface border border-white/5">
              <CardBody className="p-6 space-y-4">
                <Input
                  label="Source URL"
                  placeholder="https://gogoanime..."
                  variant="bordered"
                  classNames={{
                    inputWrapper: "bg-background/50 border-white/10",
                  }}
                />
                <div className="flex gap-4">
                  <Select
                    label="Provider"
                    placeholder="Select provider"
                    variant="bordered"
                    className="max-w-xs"
                  >
                    <SelectItem key="gogo">GogoAnime</SelectItem>
                    <SelectItem key="zoro">Zoro/HiAnime</SelectItem>
                    <SelectItem key="9anime">9Anime</SelectItem>
                  </Select>
                  <Button color="primary" size="lg" className="flex-1">
                    Scrape & Download
                  </Button>
                </div>
              </CardBody>
            </Card>
          </div>
        </Tab>
      </Tabs>
    </div>
  );
}
