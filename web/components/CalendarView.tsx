"use client";
import { useEffect, useState, useCallback } from "react";
import { ChevronLeft, ChevronRight, RefreshCw } from "lucide-react";
import { api, Event } from "@/lib/api";
import EventTypeTag from "@/components/EventTypeTag";

const TYPE_DOT: Record<string, string> = {
  appointment: "bg-indigo-400",
  scan: "bg-pink-400",
  vet: "bg-emerald-400",
  birthday: "bg-amber-400",
  other: "bg-gray-400",
};

function formatTime(timeStr: string | null) {
  if (!timeStr) return null;
  const [h, m] = timeStr.split(":");
  const hour = parseInt(h);
  return `${hour % 12 || 12}:${m}${hour >= 12 ? "pm" : "am"}`;
}

interface Props {
  member: string;
}

export default function CalendarView({ member }: Props) {
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const [currentDate, setCurrentDate] = useState(new Date(today.getFullYear(), today.getMonth(), 1));
  const [events, setEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedDate, setSelectedDate] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.events.list(member);
      setEvents(data);
    } finally {
      setLoading(false);
    }
  }, [member]);

  useEffect(() => { load(); }, [load]);

  const year = currentDate.getFullYear();
  const month = currentDate.getMonth();

  const firstDay = new Date(year, month, 1);
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  // Monday-first offset: Sunday=0 becomes 6, Monday=1 becomes 0, etc.
  const startOffset = (firstDay.getDay() + 6) % 7;

  const eventsByDate = events.reduce<Record<string, Event[]>>((acc, ev) => {
    const key = ev.date.slice(0, 10);
    if (!acc[key]) acc[key] = [];
    acc[key].push(ev);
    return acc;
  }, {});

  const selectedEvents = selectedDate ? (eventsByDate[selectedDate] ?? []) : [];

  const goMonth = (delta: number) => {
    setCurrentDate(d => new Date(d.getFullYear(), d.getMonth() + delta, 1));
    setSelectedDate(null);
  };

  const monthLabel = currentDate.toLocaleDateString("en-AU", { month: "long", year: "numeric" });

  const cells: (number | null)[] = [
    ...Array(startOffset).fill(null),
    ...Array.from({ length: daysInMonth }, (_, i) => i + 1),
  ];
  // Pad to full weeks
  while (cells.length % 7 !== 0) cells.push(null);

  const DAY_HEADERS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

  return (
    <div className="flex flex-col h-full">
      {/* Month navigation */}
      <div className="flex items-center justify-between px-4 py-3 bg-white/50 border-b border-white/60">
        <button onClick={() => goMonth(-1)} className="p-2 rounded-xl hover:bg-white/60 text-text-secondary transition-colors">
          <ChevronLeft size={20} />
        </button>
        <h2 className="text-base font-semibold text-text-primary">{monthLabel}</h2>
        <button onClick={() => goMonth(1)} className="p-2 rounded-xl hover:bg-white/60 text-text-secondary transition-colors">
          <ChevronRight size={20} />
        </button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center flex-1">
          <RefreshCw className="animate-spin text-accent" size={28} />
        </div>
      ) : (
        <div className="flex-1 overflow-auto p-4 space-y-4">
          {/* Day headers */}
          <div className="grid grid-cols-7 gap-1 mb-1">
            {DAY_HEADERS.map(d => (
              <div key={d} className="text-center text-xs font-semibold text-text-secondary py-1">{d}</div>
            ))}
          </div>

          {/* Calendar grid */}
          <div className="grid grid-cols-7 gap-1">
            {cells.map((day, idx) => {
              if (day === null) {
                return <div key={`empty-${idx}`} />;
              }
              const dateKey = `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
              const dayEvents = eventsByDate[dateKey] ?? [];
              const isToday = new Date(year, month, day).getTime() === today.getTime();
              const isSelected = selectedDate === dateKey;

              return (
                <button
                  key={dateKey}
                  onClick={() => setSelectedDate(isSelected ? null : dateKey)}
                  className={`
                    relative flex flex-col items-center rounded-xl p-1.5 min-h-[60px] transition-colors text-left
                    ${isSelected ? "bg-accent/20 ring-1 ring-accent" : "hover:bg-white/60"}
                  `}
                >
                  <span className={`
                    text-sm font-medium w-7 h-7 flex items-center justify-center rounded-full
                    ${isToday ? "bg-accent text-white" : "text-text-primary"}
                  `}>
                    {day}
                  </span>
                  {dayEvents.length > 0 && (
                    <div className="flex flex-wrap gap-0.5 mt-1 justify-center">
                      {dayEvents.slice(0, 3).map(ev => (
                        <span
                          key={ev.id}
                          className={`w-1.5 h-1.5 rounded-full ${TYPE_DOT[ev.type] ?? TYPE_DOT.other}`}
                        />
                      ))}
                      {dayEvents.length > 3 && (
                        <span className="text-[9px] text-text-secondary leading-none">+{dayEvents.length - 3}</span>
                      )}
                    </div>
                  )}
                </button>
              );
            })}
          </div>

          {/* Selected date panel */}
          {selectedDate && (
            <div className="card mt-2">
              <h3 className="text-sm font-semibold text-text-primary mb-3">
                {new Date(selectedDate + "T00:00:00").toLocaleDateString("en-AU", { weekday: "long", day: "numeric", month: "long" })}
              </h3>
              {selectedEvents.length === 0 ? (
                <p className="text-sm text-text-secondary">No events on this day.</p>
              ) : (
                <div className="space-y-2">
                  {selectedEvents.map(ev => (
                    <div key={ev.id} className="p-3 rounded-xl bg-white/50">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-medium text-text-primary text-sm">{ev.title}</span>
                        <EventTypeTag type={ev.type} />
                      </div>
                      {ev.time && (
                        <p className="text-xs text-text-secondary mt-1">{formatTime(ev.time)}</p>
                      )}
                      {ev.notes && (
                        <p className="text-xs text-text-secondary mt-1">{ev.notes}</p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
