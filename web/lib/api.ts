const API_BASE =
  typeof window === "undefined"
    ? (process.env.API_URL || "http://localhost:8000")
    : "/api/proxy";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...options?.headers },
  });
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json();
}

export const api = {
  events: {
    list: (member?: string) => request<Event[]>(member ? `/events?member=${encodeURIComponent(member)}` : "/events"),
    upcoming: () => request<Event[]>("/events/upcoming"),
    create: (body: EventCreate) =>
      request<Event>("/events", { method: "POST", body: JSON.stringify(body) }),
    update: (id: number, body: Partial<EventCreate>) =>
      request<Event>(`/events/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
    delete: (id: number) =>
      request<{ ok: boolean }>(`/events/${id}`, { method: "DELETE" }),
  },
  bills: {
    list: () => request<Bill[]>("/bills"),
    upcoming: () => request<Bill[]>("/bills/upcoming"),
    create: (body: BillCreate) =>
      request<Bill>("/bills", { method: "POST", body: JSON.stringify(body) }),
    toggle: (id: number) =>
      request<Bill>(`/bills/${id}/toggle`, { method: "PATCH", body: JSON.stringify({}) }),
    update: (id: number, body: Partial<BillCreate>) =>
      request<Bill>(`/bills/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
    delete: (id: number) =>
      request<{ ok: boolean }>(`/bills/${id}`, { method: "DELETE" }),
  },
  meals: {
    currentWeek: () => request<MealWeek>("/meals/current-week"),
    reroll: (day: string) =>
      request<MealRecipe>(`/meals/reroll/${day}`, { method: "POST" }),
    sendShoppingList: () =>
      request<{ ok: boolean }>("/meals/send-shopping-list", { method: "POST" }),
  },
};

export interface Event {
  id: number;
  title: string;
  date: string;
  time: string | null;
  type: string;
  notes: string | null;
  family_member: string | null;
  created_at: string;
}

export interface EventCreate {
  title: string;
  date: string;
  time?: string;
  type?: string;
  notes?: string;
  family_member?: string;
}

export interface Bill {
  id: number;
  name: string;
  amount: number | null;
  due_date: string;
  paid: boolean;
  category: string;
  recurring: boolean;
  created_at: string;
}

export interface BillCreate {
  name: string;
  amount?: number;
  due_date: string;
  category?: string;
  recurring?: boolean;
}

export interface MealWeek {
  week_start: string;
  meals: {
    monday: MealRecipe | null;
    tuesday: MealRecipe | null;
    wednesday: MealRecipe | null;
    thursday: MealRecipe | null;
    friday: MealRecipe | null;
  };
}

export interface MealRecipe {
  id: number;
  title: string;
  url: string;
  image_url: string | null;
  category: string | null;
}
