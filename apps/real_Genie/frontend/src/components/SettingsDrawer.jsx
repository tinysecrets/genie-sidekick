import { useState } from "react";
import { X, Settings, RotateCcw } from "lucide-react";
import { api } from "@/lib/api";

export default function SettingsDrawer({ open, onClose, persona, defaultPersona, onSaved }) {
  const [value, setValue] = useState(persona || "");
  const [saving, setSaving] = useState(false);

  const save = async () => {
    setSaving(true);
    try {
      const { data } = await api.put("/settings/persona", { persona: value });
      onSaved(data.persona);
      onClose();
    } finally {
      setSaving(false);
    }
  };

  const resetDefault = () => setValue(defaultPersona || "");

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center px-4">
      <div className="absolute inset-0 bg-black/30" onClick={onClose} />
      <div
        data-testid="settings-drawer"
        className="relative bg-[#F9F8F6] border border-[#E3E0D8] rounded-2xl shadow-xl max-w-lg w-full p-6 md:p-8"
      >
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2 text-[#2C2C28]">
            <Settings size={18} className="text-[#D05C42]" />
            <h2 className="font-heading text-2xl">Shape Ember</h2>
          </div>
          <button onClick={onClose} className="text-[#7A7A71] hover:text-[#2C2C28]" aria-label="Close" data-testid="close-settings">
            <X size={18} />
          </button>
        </div>
        <p className="text-sm text-[#7A7A71] font-body mb-5 leading-relaxed">
          Tell Ember how to be with you. Tone, style, what to call you, what to avoid.
          <br />
          The honesty rules are non-negotiable — they apply on top of whatever you write here.
        </p>

        <textarea
          data-testid="persona-textarea"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          rows={6}
          maxLength={1000}
          placeholder={defaultPersona}
          className="w-full bg-white border border-[#E3E0D8] rounded-xl px-4 py-3 font-body text-[15px] text-[#2C2C28] placeholder:text-[#A0A095] focus:outline-none focus:border-[#D05C42] focus:ring-2 focus:ring-[#D05C42]/20 resize-none"
        />
        <div className="flex items-center justify-between mt-1">
          <button
            onClick={resetDefault}
            className="text-xs text-[#7A7A71] hover:text-[#D05C42] font-body flex items-center gap-1"
            data-testid="reset-persona"
          >
            <RotateCcw size={12} /> reset to default
          </button>
          <span className="text-xs text-[#A0A095] font-body">{value.length}/1000</span>
        </div>

        <div className="flex gap-2 mt-6 justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-body text-[#7A7A71] hover:text-[#2C2C28]"
          >
            Cancel
          </button>
          <button
            data-testid="save-persona"
            onClick={save}
            disabled={saving}
            className="px-5 py-2 rounded-full bg-[#D05C42] text-white hover:bg-[#BA4C33] transition-colors text-sm font-body disabled:opacity-50"
          >
            {saving ? "Saving..." : "Save"}
          </button>
        </div>
      </div>
    </div>
  );
}
