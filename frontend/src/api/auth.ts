import { useQuery } from "@tanstack/react-query";

import type { MemberDetail } from "../types";
import { ApiClientError, api } from "./client";

export function useMe() {
  return useQuery({
    queryKey: ["me"],
    queryFn: async (): Promise<MemberDetail | null> => {
      try {
        const r = await api.get<{ member: MemberDetail }>("/auth/me");
        return r.member;
      } catch (e) {
        if (e instanceof ApiClientError && e.status === 401) return null;
        throw e;
      }
    },
  });
}

export const requestLink = (email: string) =>
  api.post<{ status: string }>("/auth/request-link", { email });

export const completeCallback = (token: string) =>
  api.get<{ member: MemberDetail }>(`/auth/callback?token=${encodeURIComponent(token)}`);

export const logout = () => api.post<void>("/auth/logout");
