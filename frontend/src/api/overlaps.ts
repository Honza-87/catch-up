import { api } from "./client";
import type { Overlap } from "../types";

export const listMine = () => api.get<{ overlaps: Overlap[] }>("/overlaps/me").then((r) => r.overlaps);
