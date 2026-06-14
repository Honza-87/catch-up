export interface Place {
  city: string;
  country_code: string;
  country_name: string;
  lat: number;
  lng: number;
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

export interface MemberDetail extends MemberSummary {
  email: string;
  note: string | null;
  created_at: string;
}

export interface ProfileUpdate {
  display_name?: string | null;
  job_title?: string | null;
  company?: string | null;
  note?: string | null;
  whatsapp_e164?: string | null;
  home_place?: Place | null;
}
