import { useEffect, useRef, useState, useCallback } from "react";
import { Mic, MicOff, Radio } from "lucide-react";
import { api } from "@/lib/api";

export async function speakEmber(text) {
  const clean = (text || "").replace(/[*_#`]/g, "").trim();
  if (!clean) return;
  try {
    await api.post("/voice/speak", { text: clean }, { timeout: 30000 });
  } catch (e) {
    console.error("Ember voice playback failed", e);
    if ("speechSynthesis" in window) {
      window.speechSynthesis.cancel();
      const u = new SpeechSynthesisUtterance(clean);
      const voices = window.speechSynthesis.getVoices?.() || [];
      u.voice = voices.find(v => /^en(-US)?/i.test(v.lang)) || voices.find(v => /^en/i.test(v.lang)) || null;
      u.lang = u.voice?.lang || "en-US";
      u.rate = 0.98; u.pitch = 1.0; u.volume = 1.0;
      window.speechSynthesis.speak(u);
    }
  }
}

export default function VoiceControls({ onSend, disabled, onVoiceModeChange }) {
  const [live, setLive] = useState(false);
  const [recording, setRecording] = useState(false);
  const [status, setStatus] = useState("Voice off");
  const recorderRef = useRef(null);
  const streamRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const rafRef = useRef(null);
  const chunksRef = useRef([]);
  const speechStartedRef = useRef(false);
  const silenceSinceRef = useRef(null);
  const liveRef = useRef(false);

  const cleanupAudio = useCallback(() => {
    if (rafRef.current) cancelAnimationFrame(rafRef.current);
    rafRef.current = null;
    if (audioContextRef.current) audioContextRef.current.close().catch(() => {});
    audioContextRef.current = null;
    analyserRef.current = null;
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
  }, []);

  const transcribe = useCallback(async (blob) => {
    if (!blob || blob.size < 1500) return;
    setStatus("Understanding…");
    const form = new FormData();
    form.append("audio", blob, "ember-voice.webm");
    try {
      const { data } = await api.post("/voice/transcribe", form, {
        headers: { "Content-Type": "multipart/form-data" },
        timeout: 30000,
      });
      const text = (data.text || "").trim();
      if (text) {
        onSend(text);
        setStatus(liveRef.current ? "Listening…" : "Voice ready");
      } else {
        setStatus(liveRef.current ? "Listening…" : "No speech heard");
      }
    } catch (e) {
      console.error("Ember voice transcription failed", e);
      setStatus("Voice error — try again");
    }
  }, [onSend]);

  const startRecording = useCallback(async () => {
    if (disabled || recording) return;
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mime = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
        ? "audio/webm;codecs=opus"
        : "audio/webm";
      const recorder = new MediaRecorder(stream, { mimeType: mime });
      recorderRef.current = recorder;
      streamRef.current = stream;
      chunksRef.current = [];
      speechStartedRef.current = false;
      silenceSinceRef.current = null;
      recorder.ondataavailable = (e) => { if (e.data.size) chunksRef.current.push(e.data); };
      recorder.onstop = async () => {
        const blob = new Blob(chunksRef.current, { type: mime });
        cleanupAudio();
        setRecording(false);
        await transcribe(blob);
        if (liveRef.current && !disabled) {
          setTimeout(() => startRecording(), 250);
        }
      };
      recorder.start(150);
      setRecording(true);
      setStatus("Listening…");

      const ctx = new AudioContext();
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 1024;
      const source = ctx.createMediaStreamSource(stream);
      source.connect(analyser);
      audioContextRef.current = ctx;
      analyserRef.current = analyser;
      const data = new Uint8Array(analyser.fftSize);

      const monitor = () => {
        if (!recorderRef.current || recorderRef.current.state !== "recording") return;
        analyser.getByteTimeDomainData(data);
        let sum = 0;
        for (let i = 0; i < data.length; i++) {
          const n = (data[i] - 128) / 128;
          sum += n * n;
        }
        const rms = Math.sqrt(sum / data.length);
        if (rms > 0.025) {
          speechStartedRef.current = true;
          silenceSinceRef.current = null;
        } else if (speechStartedRef.current) {
          if (!silenceSinceRef.current) silenceSinceRef.current = Date.now();
          if (Date.now() - silenceSinceRef.current > 1000) {
            recorder.stop();
            return;
          }
        }
        rafRef.current = requestAnimationFrame(monitor);
      };
      rafRef.current = requestAnimationFrame(monitor);
    } catch (e) {
      console.error("Ember microphone error", e);
      cleanupAudio();
      setRecording(false);
      setStatus("Microphone permission needed");
    }
  }, [cleanupAudio, disabled, recording, transcribe]);

  const stopRecording = useCallback(() => {
    liveRef.current = false;
    setLive(false);
    onVoiceModeChange?.(false);
    if (recorderRef.current?.state === "recording") recorderRef.current.stop();
    else cleanupAudio();
    setStatus("Voice off");
  }, [cleanupAudio, onVoiceModeChange]);

  const toggleLive = useCallback(async () => {
    if (liveRef.current) {
      stopRecording();
      return;
    }
    liveRef.current = true;
    setLive(true);
    onVoiceModeChange?.(true);
    if (window.speechSynthesis) window.speechSynthesis.getVoices();
    await startRecording();
  }, [onVoiceModeChange, startRecording, stopRecording]);

  useEffect(() => {
    return () => {
      liveRef.current = false;
      if (recorderRef.current?.state === "recording") recorderRef.current.stop();
      cleanupAudio();
    };
  }, [cleanupAudio]);

  return (
    <div className="flex items-center gap-2 mr-1">
      <button
        type="button"
        onClick={toggleLive}
        disabled={disabled}
        data-testid="live-voice-button"
        className={`h-10 px-3 rounded-full border flex items-center gap-2 text-xs font-body transition-all ${
          live ? "bg-[#D05C42] text-white border-[#D05C42]" : "bg-[#F8F6F1] text-[#4A4A44] border-[#E3E0D8] hover:border-[#D05C42]"
        }`}
        aria-label={live ? "Stop Ember Live voice" : "Start Ember Live voice"}
      >
        <Radio size={15} className={live ? "animate-pulse" : ""} />
        Live
      </button>
      <button
        type="button"
        onClick={recording ? stopRecording : startRecording}
        disabled={disabled}
        data-testid="voice-microphone-button"
        className={`w-10 h-10 rounded-full flex items-center justify-center transition-colors ${
          recording ? "bg-[#2C2C28] text-white" : "bg-[#F8F6F1] text-[#4A4A44] border border-[#E3E0D8] hover:border-[#D05C42]"
        }`}
        aria-label={recording ? "Stop recording" : "Talk to Ember"}
        title={status}
      >
        {recording ? <MicOff size={16} /> : <Mic size={16} />}
      </button>
    </div>
  );
}
