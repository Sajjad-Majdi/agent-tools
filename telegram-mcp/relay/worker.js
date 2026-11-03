// Optional relay for the user's own Telegram client (tg-mcp) on networks where Telegram is blocked.
//
// /<SECRET>/<dc>/apiws  ->  wss://<dc>.web.telegram.org/apiws (MTProto over WebSocket).
// The upstream response is returned as is, so Cloudflare pipes the socket with no Worker CPU per frame.
// Anything without the secret gets 404, so this is not an open proxy.

const DCS = new Set(["pluto", "venus", "aurora", "vesta", "flora"]);

export default {
  async fetch(req, env) {
    const url = new URL(req.url);
    const parts = url.pathname.split("/");
    const secret = env.RELAY_SECRET;
    if (!secret) return new Response("not configured", { status: 500 });

    if (parts[1] === secret) {
      const what = parts[2] || "";
      const dc = what.replace(/-1$/, "");
      if (DCS.has(dc) && parts[3] === "apiws" && parts.length === 4) {
        if (req.headers.get("Upgrade") !== "websocket") return new Response("ws only", { status: 426 });
        const headers = new Headers(req.headers);
        headers.delete("host");
        headers.set("Origin", "https://web.telegram.org");
        return fetch(`https://${what}.web.telegram.org/apiws`, { headers });
      }
      return new Response("not found", { status: 404 });
    }

    return new Response("not found", { status: 404 });
  },
};
