"use client";

import { Card, CardBody, Button, Chip } from "@nextui-org/react";

const content = [
  {
    id: 1,
    title: "Sousou no Frieren",
    type: "TV",
    episodes: 28,
    status: "Airing",
  },
  { id: 2, title: "One Piece", type: "TV", episodes: 1092, status: "Airing" },
  {
    id: 3,
    title: "Attack on Titan",
    type: "TV",
    episodes: 89,
    status: "Finished",
  },
];

export default function AdminContentPage() {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-foreground">
          Content Management
        </h1>
        <div className="flex gap-2">
          <Button variant="flat">Sync Jikan</Button>
          <Button color="primary">Add Anime</Button>
        </div>
      </div>

      <Card className="bg-surface border border-white/5">
        <CardBody className="p-0">
          <table className="w-full text-left">
            <thead className="border-b border-white/10 bg-white/5">
              <tr>
                <th className="p-4 text-sm font-semibold text-foreground/70">
                  Title
                </th>
                <th className="p-4 text-sm font-semibold text-foreground/70">
                  Type
                </th>
                <th className="p-4 text-sm font-semibold text-foreground/70">
                  Episodes
                </th>
                <th className="p-4 text-sm font-semibold text-foreground/70">
                  Status
                </th>
                <th className="p-4 text-sm font-semibold text-foreground/70">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody>
              {content.map((item) => (
                <tr
                  key={item.id}
                  className="border-b border-white/5 hover:bg-white/5 transition-colors"
                >
                  <td className="p-4 font-medium text-foreground">
                    {item.title}
                  </td>
                  <td className="p-4 text-foreground/70">{item.type}</td>
                  <td className="p-4 text-foreground/70">{item.episodes}</td>
                  <td className="p-4">
                    <Chip
                      size="sm"
                      variant="flat"
                      color={item.status === "Airing" ? "success" : "default"}
                    >
                      {item.status}
                    </Chip>
                  </td>
                  <td className="p-4">
                    <Button size="sm" variant="light" color="primary">
                      Edit
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardBody>
      </Card>
    </div>
  );
}
