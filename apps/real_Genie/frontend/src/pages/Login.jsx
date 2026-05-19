import { Sparkles } from "lucide-react";

// REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
function startGoogleLogin() {
  const redirectUrl = window.location.origin + "/";
  window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
}

export default function Login() {
  return (
    <div className="min-h-screen w-full bg-[#F9F8F6] flex items-center justify-center px-6 relative overflow-hidden">
      <div
        aria-hidden
        className="absolute -top-40 -right-40 w-[520px] h-[520px] rounded-full opacity-30"
        style={{
          background: "radial-gradient(circle, #D05C42 0%, rgba(208,92,66,0) 70%)",
        }}
      />
      <div
        aria-hidden
        className="absolute -bottom-40 -left-40 w-[520px] h-[520px] rounded-full opacity-20"
        style={{
          background: "radial-gradient(circle, #8C9F7B 0%, rgba(140,159,123,0) 70%)",
        }}
      />

      <div className="relative max-w-md w-full text-center">
        <div className="mb-6 inline-flex items-center gap-2 text-[#D05C42] font-body text-xs uppercase tracking-[0.3em]">
          <Sparkles size={14} /> Ember
        </div>
        <h1 className="font-heading font-light text-5xl md:text-6xl text-[#2C2C28] leading-[1.05] tracking-tight">
          A real one.
          <br />
          <span className="italic text-[#D05C42]">Not a script.</span>
        </h1>
        <p className="font-ai text-[19px] text-[#4a4a44] mt-7 leading-relaxed">
          Honest, remembers you, pushes back when you're wrong, says <em>"I don't know"</em> when it doesn't.
        </p>

        <button
          data-testid="google-login-button"
          onClick={startGoogleLogin}
          className="mt-10 w-full flex items-center justify-center gap-3 bg-[#2C2C28] text-white rounded-full px-6 py-3.5 hover:bg-[#1a1a17] transition-colors font-body text-sm shadow-sm"
        >
          <GoogleG />
          Continue with Google
        </button>

        <p className="text-[11px] text-[#7A7A71] font-body mt-6 leading-relaxed">
          Your conversations and memories sync across devices.
          <br />
          Add to your home screen for the full app feel.
        </p>
      </div>
    </div>
  );
}

function GoogleG() {
  return (
    <svg width="18" height="18" viewBox="0 0 48 48" aria-hidden>
      <path fill="#FFC107" d="M43.6 20.5H42V20H24v8h11.3c-1.6 4.7-6 8-11.3 8-6.6 0-12-5.4-12-12s5.4-12 12-12c3.1 0 5.9 1.2 8 3.1l5.7-5.7C34 6.3 29.3 4.5 24 4.5 13.2 4.5 4.5 13.2 4.5 24S13.2 43.5 24 43.5 43.5 34.8 43.5 24c0-1.2-.1-2.3-.4-3.5z"/>
      <path fill="#FF3D00" d="M6.3 14.7l6.6 4.8C14.6 16 18.9 13 24 13c3.1 0 5.9 1.2 8 3.1l5.7-5.7C34 6.3 29.3 4.5 24 4.5 16.2 4.5 9.5 9 6.3 14.7z"/>
      <path fill="#4CAF50" d="M24 43.5c5.2 0 9.9-1.8 13.5-4.7l-6.2-5.1c-2 1.5-4.5 2.4-7.3 2.4-5.3 0-9.7-3.3-11.3-8l-6.5 5C9.4 39 16.1 43.5 24 43.5z"/>
      <path fill="#1976D2" d="M43.6 20.5H42V20H24v8h11.3c-.8 2.3-2.3 4.3-4.2 5.6l6.2 5.1C40.7 35.5 43.5 30.2 43.5 24c0-1.2-.1-2.3-.4-3.5z"/>
    </svg>
  );
}
