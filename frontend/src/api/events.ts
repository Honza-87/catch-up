import { api } from "./client";
import type { EventCreate, EventUpdate, SignificantEvent } from "../types";

export const listMine = () => api.get<{ events: SignificantEvent[] }>("/events/me").then((r) => r.events);

export const listAllUpcoming = () => api.get<{ events: SignificantEvent[] }>("/events").then((r) => r.events);

export const create = (data: EventCreate) =>
  api.post<{ event: SignificantEvent }>("/events", data).then((r) => r.event);

export const update = (id: string, data: EventUpdate) =>
  api.patch<{ event: SignificantEvent }>(`/events/${id}`, data).then((r) => r.event);

export const remove = (id: string) => api.del<void>(`/events/${id}`);
