"use client";
import { useState } from "react";
import { X } from "lucide-react";
import { api, BillCreate } from "@/lib/api";

interface Props {
  onClose: () => void;
  onSaved: () => void;
}

export default function AddBillModal({ onClose, onSaved }: Props) {
  const [form, setForm] = useState<BillCreate>({
    name: "",
    amount: undefined,
    due_date: "",
    category: "utilities",
    recurring: false,
  });
  const [saving, setSaving] = useState(false);

  const save = async () => {
    if (!form.name || !form.due_date) return;
    setSaving(true);
    try {
      await api.bills.create(form);
      onSaved();
      onClose();
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4">
      <div className="w-full max-w-md card">
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-lg font-semibold text-text-primary">Add Bill</h2>
          <button onClick={onClose} className="p-1 rounded-lg hover:bg-gray-100">
            <X size={18} />
          </button>
        </div>

        <div className="space-y-4">
          <div>
            <label className="label">Bill name</label>
            <input className="input" placeholder="e.g. Electricity, Internet" value={form.name}
              onChange={e => setForm(f => ({ ...f, name: e.target.value }))} />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">Amount (optional)</label>
              <input type="number" step="0.01" className="input" placeholder="0.00"
                value={form.amount ?? ""}
                onChange={e => setForm(f => ({ ...f, amount: e.target.value ? parseFloat(e.target.value) : undefined }))} />
            </div>
            <div>
              <label className="label">Due date</label>
              <input type="date" className="input" value={form.due_date}
                onChange={e => setForm(f => ({ ...f, due_date: e.target.value }))} />
            </div>
          </div>

          <div>
            <label className="label">Category</label>
            <select className="input" value={form.category}
              onChange={e => setForm(f => ({ ...f, category: e.target.value }))}>
              <option value="utilities">Utilities</option>
              <option value="insurance">Insurance</option>
              <option value="subscriptions">Subscriptions</option>
              <option value="rent">Rent / Mortgage</option>
              <option value="health">Health</option>
              <option value="other">Other</option>
            </select>
          </div>

          <label className="flex items-center gap-3 cursor-pointer">
            <input type="checkbox" className="w-4 h-4 rounded accent-accent"
              checked={form.recurring}
              onChange={e => setForm(f => ({ ...f, recurring: e.target.checked }))} />
            <span className="text-sm text-text-secondary">Recurring bill</span>
          </label>
        </div>

        <div className="flex gap-3 mt-6">
          <button className="btn-ghost flex-1" onClick={onClose}>Cancel</button>
          <button className="btn-primary flex-1" onClick={save} disabled={saving || !form.name || !form.due_date}>
            {saving ? "Saving..." : "Save Bill"}
          </button>
        </div>
      </div>
    </div>
  );
}
