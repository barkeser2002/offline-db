"use client";

import { Card, CardBody, Avatar, Chip, Button } from "@nextui-org/react";

const users = [
  {
    id: 1,
    name: "Barış Keser",
    role: "Admin",
    status: "Active",
    email: "baris@example.com",
  },
  {
    id: 2,
    name: "AnimeFan99",
    role: "User",
    status: "Active",
    email: "fan99@example.com",
  },
  {
    id: 3,
    name: "OtakuKing",
    role: "Premium",
    status: "Active",
    email: "otaku@example.com",
  },
  {
    id: 4,
    name: "Guest_123",
    role: "User",
    status: "Inactive",
    email: "guest@example.com",
  },
];

export default function AdminUsersPage() {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-foreground">User Management</h1>
        <Button color="primary">Add User</Button>
      </div>

      <Card className="bg-surface border border-white/5">
        <CardBody className="p-0">
          <table className="w-full text-left">
            <thead className="border-b border-white/10 bg-white/5">
              <tr>
                <th className="p-4 text-sm font-semibold text-foreground/70">
                  User
                </th>
                <th className="p-4 text-sm font-semibold text-foreground/70">
                  Role
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
              {users.map((user) => (
                <tr
                  key={user.id}
                  className="border-b border-white/5 hover:bg-white/5 transition-colors"
                >
                  <td className="p-4">
                    <div className="flex items-center gap-3">
                      <Avatar name={user.name} size="sm" />
                      <div>
                        <p className="font-medium text-foreground">
                          {user.name}
                        </p>
                        <p className="text-xs text-foreground/50">
                          {user.email}
                        </p>
                      </div>
                    </div>
                  </td>
                  <td className="p-4">
                    <Chip
                      size="sm"
                      variant="flat"
                      color={
                        user.role === "Admin"
                          ? "warning"
                          : user.role === "Premium"
                            ? "secondary"
                            : "default"
                      }
                    >
                      {user.role}
                    </Chip>
                  </td>
                  <td className="p-4">
                    <Chip
                      size="sm"
                      variant="dot"
                      color={user.status === "Active" ? "success" : "default"}
                    >
                      {user.status}
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
