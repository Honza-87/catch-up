import { api } from "./client";
import type { MemberDetail, MemberSummary, Place, ProfileUpdate } from "../types";

export const updateProfile = (data: ProfileUpdate) =>
  api.patch<{ member: MemberDetail }>("/members/me", data).then((r) => r.member);

export const uploadPhoto = (file: File) => {
  const form = new FormData();
  form.append("file", file);
  return api.postForm<{ photo_url: string }>("/members/me/photo", form);
};

export const deletePhoto = () => api.del<void>("/members/me/photo");

export const searchPlaces = (q: string, country?: string) => {
  const params = new URLSearchParams({ q });
  if (country) params.set("country", country);
  return api.get<{ places: Place[] }>(`/places/search?${params.toString()}`).then((r) => r.places);
};

export const fetchMembers = () =>
  api.get<{ members: MemberSummary[] }>("/members").then((r) => r.members);

export const fetchMember = (id: string) =>
  api.get<{ member: MemberDetail }>(`/members/${id}`).then((r) => r.member);
