"use client";
import { useState } from "react";
import { X } from "lucide-react";
import { api, EventCreate } from "@/lib/api";

interface Props {
  onClose: () => void;
  onSaved: () => void;
}

export default function AddEventModal({ onClose, onSaved }: Props) {
  const [form, setForm] = useState<EventCreate>({
    title: "",
    date: "",
    time: "",
    type: "appointment",
    notes: "",
    family_member: "",
  });
  const [saving, setSaving] = useState(false);

  const save = async () => {
    if (!form.title || !form.date) return;
    setSaving(true);
    try {
      await api.events.create({
        ...form,
        time: form.time || undefined,
        notes: form.notes || undefined,
        family_member: form.family_member || undefined,
      });
      onSaved();
      onClose();
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 dark:bg-black/60 p-4">
      <div className="w-full max-w-md card">
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-lg font-semibold text-text-primary">Add Event</h2>
          <button onClick={onClose} className="p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-white/10">
            <X size={18} />
          </button>
        </div>

        <div className="space-y-4">
          <div>
            <label className="label">Title</label>
            <input className="input" placeholder="e.g. Baby scan, Vet appointment" value={form.title}
              onChange={e => setForm(f => ({ ...f, title: e.target.value }))} />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Date</label>
              <input type="date" className="input" value={form.date}
                onChange={e => setForm(f => ({ ...f, date: e.target.value }))} />
            </div>
            <div>
              <label className="label">Time (optional)</label>
              <input type="time" className="input" value={form.time ?? ""}
                onChange={e => setForm(f => ({ ...f, time: e.target.value }))} />
            </div>
          </div>

          <div>
            <label className="label">Type</label>
            <select className="input" value={form.type}
              onChange={e => setForm(f => ({ ...f, type: e.target.value }))}>
              <option value="appointment">Appointment</option>
              <option value="scan">Scan</option>
              <option value="vet">Vet</option>
              <option value="birthday">Birthday</option>
              <option value="other">Other</option>
            </select>
          </div>

          <div>
            <label className="label">For (optional)</label>
            <select className="input" value={form.family_member ?? ""}
              onChange={e => setForm(f => ({ ...f, family_member: e.target.value }))}>
              <option value="">General / Everyone</option>
              <option value="Doug">Doug</option>
              <option value="Edina">Edina</option>
              <option value="Doggies">Doggies</option>
              <option value="Baby">Baby</option>
            </select>
          </div>

          <div>
            <label className="label">Notes (optional)</label>
            <textarea className="input resize-none" rows={2} placeholder="Any extra details..."
              value={form.notes ?? ""}
              onChange={e => setForm(f => ({ ...f, notes: e.target.value }))} />
          </div>
        </div>

        <div className="flex gap-3 mt-6">
          <button className="btn-ghost flex-1" onClick={onClose}>Cancel</button>
          <button className="btn-primary flex-1" onClick={save} disabled={saving || !form.title || !form.date}>
            {saving ? "Saving..." : "Save Event"}
          </button>
        </div>
      </div>
    </div>
  );
}
