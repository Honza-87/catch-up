import { api } from "./client";
import type { Trip, TripCreate, TripUpdate } from "../types";

export const listMine = () => api.get<{ trips: Trip[] }>("/trips/me").then((r) => r.trips);

export const listAllUpcoming = () => api.get<{ trips: Trip[] }>("/trips").then((r) => r.trips);

export const create = (data: TripCreate) =>
  api.post<{ trip: Trip }>("/trips", data).then((r) => r.trip);

export const update = (id: string, data: TripUpdate) =>
  api.patch<{ trip: Trip }>(`/trips/${id}`, data).then((r) => r.trip);

export const remove = (id: string) => api.del<void>(`/trips/${id}`);
