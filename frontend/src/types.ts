export interface Place {
  city: string;
  country_code: string;
  country_name: string;
  lat: number;
  lng: number;
}

export interface MemberLite {
  id: string;
  display_name: string | null;
  photo_url: string | null;
}

export interface MemberSummary {
  id: string;
  display_name: string | null;
  photo_url: string | null;
  home_place: Place | null;
  job_title: string | null;
  company: string | null;
  whatsapp_e164: string | null;
}

export interface Trip {
  id: string;
  member: MemberLite;
  place: Place;
  start_date: string;
  end_date: string;
  note: string | null;
}

export interface TripCreate {
  place: Place;
  start_date: string;
  end_date: string;
  note?: string | null;
}

export interface TripUpdate {
  place?: Place;
  start_date?: string;
  end_date?: string;
  note?: string | null;
}

export interface SignificantEvent {
  id: string;
  member: MemberLite;
  place: Place | null;
  title: string;
  start_date: string;
  end_date: string;
  note: string | null;
}

export interface EventCreate {
  title: string;
  start_date: string;
  end_date: string;
  note?: string | null;
}

export interface EventUpdate {
  title?: string;
  start_date?: string;
  end_date?: string;
  note?: string | null;
}

export interface MemberDetail extends MemberSummary {
  email: string;
  note: string | null;
  digest_opt_out: boolean;
  created_at: string;
  trips: Trip[];
  events: SignificantEvent[];
}

export interface Overlap {
  id: string;
  other_member: MemberLite;
  kind: "trip-trip" | "trip-home";
  strength: "strong" | "medium";
  place: Place | null;
  country_code: string;
  start_date: string;
  end_date: string;
}

export interface ProfileUpdate {
  display_name?: string | null;
  job_title?: string | null;
  company?: string | null;
  note?: string | null;
  whatsapp_e164?: string | null;
  home_place?: Place | null;
  digest_opt_out?: boolean;
}
