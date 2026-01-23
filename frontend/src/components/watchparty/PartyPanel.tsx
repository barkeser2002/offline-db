"use client";

import React, { useState, useRef, useEffect } from "react";
import {
  Card,
  CardBody,
  Button,
  Input,
  ScrollShadow,
  Avatar,
  Tab,
  Tabs,
} from "@nextui-org/react";

interface PartyPanelProps {
  chatMessages: any[];
  participants: any[];
  onSendMessage: (msg: string) => void;
  onSendEmote: (emote: string) => void;
  isConnected: boolean;
}

export const PartyPanel: React.FC<PartyPanelProps> = ({
  chatMessages,
  participants,
  onSendMessage,
  onSendEmote,
  isConnected,
}) => {
  const [message, setMessage] = useState("");
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatMessages]);

  const handleSend = () => {
    if (message.trim()) {
      onSendMessage(message);
      setMessage("");
    }
  };

  return (
    <div className="flex flex-col h-full bg-content1 rounded-large">
      <div className="px-4 py-2 border-b border-divider flex justify-between items-center">
        <h3 className="text-large font-bold">Watch Party</h3>
        <div
          className={`w-2 h-2 rounded-full ${isConnected ? "bg-success" : "bg-danger"}`}
        />
      </div>

      <Tabs aria-label="Party Options" className="w-full" variant="underlined">
        <Tab key="chat" title="Chat">
          <ScrollShadow className="h-[400px] p-4 flex flex-col gap-3">
            {chatMessages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex flex-col ${msg.is_system ? "items-center" : "items-start"}`}
              >
                {msg.is_system ? (
                  <span className="text-tiny text-default-400 italic">
                    {msg.message}
                  </span>
                ) : (
                  <>
                    <span className="text-tiny text-primary font-bold">
                      {msg.username}
                    </span>
                    <div className="bg-default-100 p-2 rounded-lg text-small">
                      {msg.message}
                    </div>
                  </>
                )}
              </div>
            ))}
            <div ref={chatEndRef} />
          </ScrollShadow>
          <div className="p-2 border-t border-divider flex gap-2">
            <Input
              size="sm"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSend()}
              placeholder="Type a message..."
            />
            <Button size="sm" color="primary" onPress={handleSend}>
              Send
            </Button>
          </div>
          <div className="p-2 flex gap-1 overflow-x-auto">
            {/* Quick Emotes */}
            {["🔥", "😂", "😭", "❤️", "😱"].map((emote) => (
              <Button
                key={emote}
                isIconOnly
                size="sm"
                variant="flat"
                onPress={() => onSendEmote(emote)}
              >
                {emote}
              </Button>
            ))}
          </div>
        </Tab>
        <Tab key="users" title={`Users (${participants.length})`}>
          <div className="p-4 flex flex-col gap-2">
            {participants.map((p, idx) => (
              <div key={idx} className="flex items-center gap-2">
                <Avatar name={p.username} size="sm" />
                <span className="text-small">{p.username}</span>
              </div>
            ))}
          </div>
        </Tab>
      </Tabs>
    </div>
  );
};
