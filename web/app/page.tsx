"use client";
import { useEffect, useState, useCallback } from "react";
import { Plus, Trash2, CheckCircle2, Circle, RefreshCw, ExternalLink, Send, Sun, Moon } from "lucide-react";
import { api, Event, Bill, MealWeek } from "@/lib/api";
import EventTypeTag from "@/components/EventTypeTag";
import AddEventModal from "@/components/AddEventModal";
import AddBillModal from "@/components/AddBillModal";
import CalendarView from "@/components/CalendarView";
import { useTheme } from "@/components/ThemeProvider";

const DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday"] as const;
const MEMBERS = ["Doug", "Edina", "Doggies", "Baby"] as const;

function formatDate(dateStr: string) {
  const d = new Date(dateStr + "T00:00:00");
  return d.toLocaleDateString("en-AU", { weekday: "short", day: "numeric", month: "short" });
}

function formatTime(timeStr: string | null) {
  if (!timeStr) return null;
  const [h, m] = timeStr.split(":");
  const hour = parseInt(h);
  return `${hour % 12 || 12}:${m}${hour >= 12 ? "pm" : "am"}`;
}

function daysUntil(dateStr: string) {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const target = new Date(dateStr + "T00:00:00");
  const diff = Math.round((target.getTime() - today.getTime()) / 86400000);
  if (diff === 0) return "Today";
  if (diff === 1) return "Tomorrow";
  if (diff < 0) return `${Math.abs(diff)}d overdue`;
  return `in ${diff}d`;
}

export default function Dashboard() {
  const { dark, toggle } = useTheme();
  const [events, setEvents] = useState<Event[]>([]);
  const [bills, setBills] = useState<Bill[]>([]);
  const [meals, setMeals] = useState<MealWeek | null>(null);
  const [showAddEvent, setShowAddEvent] = useState(false);
  const [showAddBill, setShowAddBill] = useState(false);
  const [rerolling, setRerolling] = useState<string | null>(null);
  const [sending, setSending] = useState(false);
  const [sendResult, setSendResult] = useState<"ok" | "error" | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [calendarMember, setCalendarMember] = useState<string | null>(null);

  const load = useCallback(async (showSpinner = false) => {
    if (showSpinner) setRefreshing(true);
    const [evRes, billRes, mealRes] = await Promise.allSettled([
      api.events.upcoming(),
      api.bills.list(),
      api.meals.currentWeek(),
    ]);
    if (evRes.status === "fulfilled") setEvents(evRes.value);
    if (billRes.status === "fulfilled") setBills(billRes.value);
    if (mealRes.status === "fulfilled") setMeals(mealRes.value);
    setLoading(false);
    setRefreshing(false);
  }, []);

  useEffect(() => {
    load();
    const interval = setInterval(() => load(), 60000);
    return () => clearInterval(interval);
  }, [load]);

  const deleteEvent = async (id: number) => {
    await api.events.delete(id);
    setEvents(ev => ev.filter(e => e.id !== id));
  };

  const toggleBill = async (id: number) => {
    const updated = await api.bills.toggle(id);
    setBills(bs => bs.map(b => b.id === id ? updated : b));
  };

  const deleteBill = async (id: number) => {
    await api.bills.delete(id);
    setBills(bs => bs.filter(b => b.id !== id));
  };

  const rerollDay = async (day: string) => {
    setRerolling(day);
    try {
      const newRecipe = await api.meals.reroll(day);
      setMeals(prev => prev ? {
        ...prev,
        meals: { ...prev.meals, [day]: newRecipe }
      } : prev);
    } finally {
      setRerolling(null);
    }
  };

  const sendShoppingList = async () => {
    setSending(true);
    setSendResult(null);
    try {
      await api.meals.sendShoppingList();
      setSendResult("ok");
    } catch {
      setSendResult("error");
    } finally {
      setSending(false);
      setTimeout(() => setSendResult(null), 4000);
    }
  };

  const selectMember = (member: string) => {
    setCalendarMember(prev => prev === member ? null : member);
  };

  const unpaidBills = bills.filter(b => !b.paid);
  const paidBills = bills.filter(b => b.paid);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <RefreshCw className="animate-spin text-accent" size={32} />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Header */}
      <header className="bg-white/50 dark:bg-white/5 backdrop-blur-md border-b border-white/60 dark:border-white/10 sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-4 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-text-primary">Harper Family</h1>
            <p className="text-sm text-text-secondary">{new Date().toLocaleDateString("en-AU", { weekday: "long", day: "numeric", month: "long" })}</p>
          </div>
          <div className="flex items-center gap-1">
            <button onClick={toggle} className="p-2 rounded-xl hover:bg-white/60 dark:hover:bg-white/10 text-text-secondary transition-colors" aria-label="Toggle theme">
              {dark ? <Sun size={18} /> : <Moon size={18} />}
            </button>
            <button onClick={() => load(true)} disabled={refreshing} className="p-2 rounded-xl hover:bg-white/60 dark:hover:bg-white/10 text-text-secondary transition-colors">
              <RefreshCw size={18} className={refreshing ? "animate-spin" : ""} />
            </button>
          </div>
        </div>
        {/* Member tabs */}
        <div className="max-w-5xl mx-auto px-4 pb-3 flex gap-2">
          {MEMBERS.map(member => (
            <button
              key={member}
              onClick={() => selectMember(member)}
              className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                calendarMember === member
                  ? "bg-accent text-white"
                  : "bg-white/60 text-text-secondary hover:bg-white/80 dark:bg-white/10 dark:hover:bg-white/20"
              }`}
            >
              {member}
            </button>
          ))}
        </div>
      </header>

      {calendarMember ? (
        <div className="flex-1 flex flex-col max-w-5xl w-full mx-auto px-4 py-4">
          <CalendarView member={calendarMember} />
        </div>
      ) : (
        <main className="max-w-5xl mx-auto px-4 py-6 space-y-6 w-full">

          {/* Upcoming Events */}
          <section className="card">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-semibold text-text-primary">Upcoming Events</h2>
              <button className="btn-primary" onClick={() => setShowAddEvent(true)}>
                <Plus size={16} /> Add
              </button>
            </div>

            {events.length === 0 ? (
              <p className="text-text-secondary text-sm text-center py-6">No upcoming events — add one above</p>
            ) : (
              <div className="space-y-2">
                {events.map(event => (
                  <div key={event.id} className="flex items-center gap-4 p-3 rounded-xl bg-white/50 hover:bg-white/80 dark:bg-white/5 dark:hover:bg-white/10 transition-colors">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-medium text-text-primary text-sm">{event.title}</span>
                        <EventTypeTag type={event.type} />
                        {event.family_member && (
                          <span className="type-badge bg-violet-100 text-violet-700">{event.family_member}</span>
                        )}
                      </div>
                      <div className="flex items-center gap-2 mt-1 text-xs text-text-secondary">
                        <span>{formatDate(event.date)}</span>
                        {event.time && <span>· {formatTime(event.time)}</span>}
                        <span className="font-medium text-accent">· {daysUntil(event.date)}</span>
                      </div>
                      {event.notes && <p className="text-xs text-text-secondary mt-1">{event.notes}</p>}
                    </div>
                    <button onClick={() => deleteEvent(event.id)}
                      className="p-1.5 rounded-lg text-text-secondary hover:text-danger hover:bg-red-50 transition-colors shrink-0">
                      <Trash2 size={16} />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </section>

          {/* Bills */}
          <section className="card">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-semibold text-text-primary">Bills</h2>
              <button className="btn-primary" onClick={() => setShowAddBill(true)}>
                <Plus size={16} /> Add
              </button>
            </div>

            {bills.length === 0 ? (
              <p className="text-text-secondary text-sm text-center py-6">No bills — add one above</p>
            ) : (
              <div className="space-y-2">
                {/* Unpaid */}
                {unpaidBills.map(bill => (
                  <div key={bill.id} className="flex items-center gap-3 p-3 rounded-xl bg-white/50 hover:bg-white/80 dark:bg-white/5 dark:hover:bg-white/10 transition-colors">
                    <button onClick={() => toggleBill(bill.id)} className="text-gray-300 hover:text-success transition-colors shrink-0">
                      <Circle size={20} />
                    </button>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-text-primary text-sm">{bill.name}</span>
                        {bill.recurring && <span className="type-badge bg-blue-50 text-blue-600">Recurring</span>}
                      </div>
                      <div className="flex items-center gap-2 mt-0.5 text-xs text-text-secondary">
                        {bill.amount && <span className="font-medium text-text-primary">${bill.amount.toFixed(2)}</span>}
                        <span>Due {formatDate(bill.due_date)}</span>
                        <span className={`font-medium ${daysUntil(bill.due_date).includes("overdue") ? "text-danger" : "text-warning"}`}>
                          · {daysUntil(bill.due_date)}
                        </span>
                      </div>
                    </div>
                    <button onClick={() => deleteBill(bill.id)}
                      className="p-1.5 rounded-lg text-text-secondary hover:text-danger hover:bg-red-50 transition-colors shrink-0">
                      <Trash2 size={16} />
                    </button>
                  </div>
                ))}

                {/* Paid */}
                {paidBills.map(bill => (
                  <div key={bill.id} className="flex items-center gap-3 p-3 rounded-xl opacity-50">
                    <button onClick={() => toggleBill(bill.id)} className="text-success shrink-0">
                      <CheckCircle2 size={20} />
                    </button>
                    <div className="flex-1 min-w-0">
                      <span className="text-sm text-text-secondary line-through">{bill.name}</span>
                      {bill.amount && <span className="text-xs text-text-secondary ml-2">${bill.amount.toFixed(2)}</span>}
                    </div>
                    <button onClick={() => deleteBill(bill.id)}
                      className="p-1.5 rounded-lg text-text-secondary hover:text-danger hover:bg-red-50 transition-colors shrink-0">
                      <Trash2 size={16} />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </section>

          {/* Meal Plan */}
          <section className="card">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-base font-semibold text-text-primary">This Week&apos;s Meals</h2>
                {meals?.week_start && (
                  <p className="text-xs text-text-secondary mt-0.5">Week of {formatDate(meals.week_start)}</p>
                )}
              </div>
              <button
                onClick={sendShoppingList}
                disabled={sending || !meals?.meals}
                className={`btn ${sendResult === "ok" ? "bg-emerald-100 text-emerald-700" : sendResult === "error" ? "bg-red-100 text-danger" : "btn-primary"}`}
              >
                <Send size={15} />
                {sending ? "Sending..." : sendResult === "ok" ? "Sent!" : sendResult === "error" ? "Failed" : "Send Shopping List"}
              </button>
            </div>

            {!meals || !meals.meals ? (
              <p className="text-text-secondary text-sm text-center py-6">No meal plan available yet</p>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {DAYS.map(day => {
                  const meal = meals.meals[day];
                  const isRerolling = rerolling === day;
                  return (
                    <div key={day} className="rounded-xl bg-violet-50/60 dark:bg-violet-950/30 p-3 relative">
                      <div className="flex items-center justify-between mb-2">
                        <p className="text-xs font-semibold uppercase tracking-wide text-text-secondary capitalize">{day}</p>
                        <button
                          onClick={() => rerollDay(day)}
                          disabled={isRerolling}
                          className="p-1 rounded-lg text-text-secondary hover:text-accent hover:bg-accent-light transition-colors"
                          title={`Reroll ${day}`}
                        >
                          <RefreshCw size={14} className={isRerolling ? "animate-spin" : ""} />
                        </button>
                      </div>
                      {isRerolling ? (
                        <div className="flex items-center justify-center h-28">
                          <RefreshCw size={20} className="animate-spin text-accent" />
                        </div>
                      ) : meal ? (
                        <div>
                          {meal.image_url && (
                            <img src={meal.image_url} alt={meal.title}
                              className="w-full h-28 object-cover rounded-lg mb-2" />
                          )}
                          <p className="text-sm font-medium text-text-primary leading-snug">{meal.title}</p>
                          <a href={meal.url} target="_blank" rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 text-xs text-accent mt-1.5 hover:underline">
                            View recipe <ExternalLink size={11} />
                          </a>
                        </div>
                      ) : (
                        <p className="text-sm text-text-secondary">—</p>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </section>

        </main>
      )}

      {showAddEvent && (
        <AddEventModal onClose={() => setShowAddEvent(false)} onSaved={load} />
      )}
      {showAddBill && (
        <AddBillModal onClose={() => setShowAddBill(false)} onSaved={load} />
      )}
    </div>
  );
}
