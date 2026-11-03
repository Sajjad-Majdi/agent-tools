import React, { createContext, useContext } from "react";
import {
  AbsoluteFill,
  Easing,
  getInputProps,
  interpolate,
  Sequence,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { Audio } from "@remotion/media";
import { loadFont as loadVazir } from "@remotion/google-fonts/Vazirmatn";
import { loadFont as loadInter } from "@remotion/google-fonts/Inter";
import { loadFont as loadMono } from "@remotion/google-fonts/JetBrainsMono";

export const FA = loadVazir("normal", {
  weights: ["400", "500", "700", "900"],
  subsets: ["arabic", "latin"],
}).fontFamily;
export const EN = loadInter("normal", {
  weights: ["400", "600", "800"],
  subsets: ["latin"],
}).fontFamily;
export const MONO = loadMono("normal", {
  weights: ["500", "700"],
  subsets: ["latin"],
}).fontFamily;

export const C = {
  bg: "#070b18",
  panel: "#0f1629",
  line: "#25304d",
  text: "#e8ecf8",
  muted: "#8b95b5",
  attn: "#4f8cff",
  ffn: "#ff9f43",
  norm: "#2ed3a0",
  pos: "#a78bfa",
  hot: "#f472b6",
  gold: "#ffd166",
  red: "#ff5c6c",
  img: "#22d3ee",
  audio: "#facc15",
};

export const LEAD = 0.5; // seconds before narration starts
export const TAIL = 0.9; // seconds after narration ends
export const FADE = 15; // transition frames

export type SceneTiming = {
  id: string;
  audio: string;
  duration: number;
  beats: number[];
  sentences: string[];
};

export const sceneFrames = (t: SceneTiming, fps: number) =>
  Math.ceil((LEAD + t.duration + TAIL) * fps);

const Ctx = createContext<{ beats: number[] }>({ beats: [] });

/** Returns a function giving eased 0..1 progress after beat `b` (+delay frames). */
export const useAt = () => {
  const frame = useCurrentFrame();
  const { beats } = useContext(Ctx);
  return (b: number, delay = 0, dur = 18) =>
    interpolate(frame - (beats[b] ?? 0) - delay, [0, dur], [0, 1], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
      easing: Easing.bezier(0.16, 1, 0.3, 1),
    });
};

/** Frames elapsed since beat `b` (can be negative). */
export const useSince = () => {
  const frame = useCurrentFrame();
  const { beats } = useContext(Ctx);
  return (b: number) => frame - (beats[b] ?? 0);
};

export const mix = (p: number, a: number, b: number) => a + (b - a) * p;

export const Reveal: React.FC<{
  p: number;
  dy?: number;
  style?: React.CSSProperties;
  children: React.ReactNode;
}> = ({ p, dy = 28, style, children }) => (
  <div
    style={{
      position: "absolute",
      opacity: p,
      translate: `0px ${(1 - p) * dy}px`,
      ...style,
    }}
  >
    {children}
  </div>
);

export const Block: React.FC<{
  x: number;
  y: number;
  w: number;
  h: number;
  color: string;
  label: React.ReactNode;
  sub?: React.ReactNode;
  p?: number;
  glow?: number;
  dim?: number;
  size?: number;
  font?: string;
}> = ({ x, y, w, h, color, label, sub, p = 1, glow = 0, dim = 0, size = 30, font }) => (
  <div
    style={{
      position: "absolute",
      left: x,
      top: y,
      width: w,
      height: h,
      opacity: p * (1 - dim * 0.75),
      scale: `${mix(p, 0.85, 1)}`,
      borderRadius: 18,
      background: `linear-gradient(160deg, ${color}33, ${color}14)`,
      border: `2px solid ${color}${glow > 0.01 ? "ff" : "99"}`,
      boxShadow: `0 0 ${glow * 50}px ${color}${Math.round(glow * 160)
        .toString(16)
        .padStart(2, "0")}`,
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      color: C.text,
      fontFamily: font ?? EN,
      fontWeight: 600,
      fontSize: size,
      textAlign: "center",
      lineHeight: 1.15,
    }}
  >
    <div>{label}</div>
    {sub ? (
      <div style={{ fontSize: size * 0.62, color: C.muted, marginTop: 6, fontWeight: 500 }}>{sub}</div>
    ) : null}
  </div>
);

export const Arrow: React.FC<{
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  p?: number;
  color?: string;
  width?: number;
  dashed?: boolean;
  curve?: number;
}> = ({ x1, y1, x2, y2, p = 1, color = C.muted, width = 4, dashed, curve = 0 }) => {
  const mx = (x1 + x2) / 2 - (y2 - y1) * curve;
  const my = (y1 + y2) / 2 + (x2 - x1) * curve;
  const d = `M ${x1} ${y1} Q ${mx} ${my} ${x2} ${y2}`;
  const len = Math.hypot(x2 - x1, y2 - y1) * (1 + Math.abs(curve));
  const ang = Math.atan2(y2 - my, x2 - mx);
  const hx = x2;
  const hy = y2;
  const s = 16;
  return (
    <svg style={{ position: "absolute", inset: 0, overflow: "visible" }} width={1920} height={1080}>
      <path
        d={d}
        fill="none"
        stroke={color}
        strokeWidth={width}
        strokeLinecap="round"
        strokeDasharray={dashed ? "10 10" : `${len} ${len}`}
        strokeDashoffset={dashed ? 0 : len * (1 - p)}
        opacity={dashed ? p : 1}
      />
      <polygon
        points={`${hx},${hy} ${hx - s * Math.cos(ang - 0.45)},${hy - s * Math.sin(ang - 0.45)} ${
          hx - s * Math.cos(ang + 0.45)
        },${hy - s * Math.sin(ang + 0.45)}`}
        fill={color}
        opacity={p > 0.9 ? (p - 0.9) * 10 : 0}
      />
    </svg>
  );
};

export const Chip: React.FC<{
  x: number;
  y: number;
  p: number;
  color?: string;
  children: React.ReactNode;
  size?: number;
  font?: string;
}> = ({ x, y, p, color = C.attn, children, size = 28, font }) => (
  <div
    style={{
      position: "absolute",
      left: x,
      top: y,
      opacity: p,
      scale: `${mix(p, 0.7, 1)}`,
      padding: "10px 22px",
      borderRadius: 999,
      background: `${color}22`,
      border: `2px solid ${color}`,
      color: C.text,
      fontFamily: font ?? EN,
      fontWeight: 600,
      fontSize: size,
      whiteSpace: "nowrap",
    }}
  >
    {children}
  </div>
);

export const FaText: React.FC<{
  x: number;
  y: number;
  w: number;
  p?: number;
  size?: number;
  color?: string;
  weight?: number;
  align?: "right" | "center" | "left";
  children: React.ReactNode;
}> = ({ x, y, w, p = 1, size = 40, color = C.text, weight = 500, align = "right", children }) => (
  <div
    dir="rtl"
    style={{
      position: "absolute",
      left: x,
      top: y,
      width: w,
      opacity: p,
      translate: `0px ${(1 - p) * 20}px`,
      fontFamily: FA,
      fontSize: size,
      fontWeight: weight,
      color,
      textAlign: align,
      lineHeight: 1.6,
    }}
  >
    {children}
  </div>
);

export const Cross: React.FC<{ x: number; y: number; w: number; h: number; p: number }> = ({ x, y, w, h, p }) => (
  <svg style={{ position: "absolute", left: x, top: y, overflow: "visible" }} width={w} height={h}>
    <line x1={0} y1={0} x2={w * p} y2={h * p} stroke={C.red} strokeWidth={8} strokeLinecap="round" />
    <line
      x1={w}
      y1={0}
      x2={w - w * Math.max(0, p * 2 - 1)}
      y2={h * Math.max(0, p * 2 - 1)}
      stroke={C.red}
      strokeWidth={8}
      strokeLinecap="round"
      opacity={p > 0.5 ? 1 : 0}
    />
  </svg>
);

const Background: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{ background: C.bg }}>
      <AbsoluteFill
        style={{
          background: `radial-gradient(900px 600px at ${20 + Math.sin(frame / 150) * 6}% 10%, #1b2a5a55, transparent 70%),
            radial-gradient(800px 600px at ${85 + Math.cos(frame / 170) * 5}% 90%, #3a1b5a44, transparent 70%)`,
        }}
      />
      <AbsoluteFill
        style={{
          backgroundImage: `linear-gradient(${C.line}33 1px, transparent 1px), linear-gradient(90deg, ${C.line}33 1px, transparent 1px)`,
          backgroundSize: "60px 60px",
          backgroundPosition: `0px ${(frame * 0.3) % 60}px`,
          maskImage: "radial-gradient(ellipse at center, black 30%, transparent 80%)",
        }}
      />
    </AbsoluteFill>
  );
};

const Caption: React.FC<{ t: SceneTiming }> = ({ t }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const sec = frame / fps - LEAD;
  if (sec < 0 || sec > t.duration + 0.2) return null;
  let i = 0;
  t.beats.forEach((b, k) => {
    if (sec >= b) i = k;
  });
  const local = sec - t.beats[i];
  const o = interpolate(local, [0, 0.25], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <div
      style={{
        position: "absolute",
        left: 0,
        right: 0,
        bottom: 34,
        display: "flex",
        justifyContent: "center",
      }}
    >
      <div
        dir="rtl"
        style={{
          maxWidth: 1600,
          padding: "12px 34px",
          borderRadius: 16,
          background: "rgba(5,8,20,0.72)",
          border: `1px solid ${C.line}`,
          fontFamily: FA,
          fontSize: 34,
          lineHeight: 1.65,
          color: C.text,
          textAlign: "center",
          opacity: o,
        }}
      >
        {t.sentences[i]}
      </div>
    </div>
  );
};

export const SceneShell: React.FC<{
  t: SceneTiming;
  index: number;
  total: number;
  title: string;
  en: string;
  children: React.ReactNode;
  hideTitle?: boolean;
}> = ({ t, index, total, title, en, children, hideTitle }) => {
  const { fps } = useVideoConfig();
  const frame = useCurrentFrame();
  const beats = t.beats.map((b) => Math.round((b + LEAD) * fps));
  const tp = interpolate(frame, [0, 18], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.bezier(0.16, 1, 0.3, 1),
  });
  return (
    <Ctx.Provider value={{ beats }}>
      <AbsoluteFill style={{ overflow: "hidden" }}>
        <Background />
        {hideTitle ? null : (
          <>
            <div
              dir="rtl"
              style={{
                position: "absolute",
                right: 90,
                top: 44,
                opacity: tp,
                translate: `${(1 - tp) * 40}px 0px`,
                fontFamily: FA,
                fontWeight: 900,
                fontSize: 60,
                color: C.text,
              }}
            >
              {title}
            </div>
            <div
              style={{
                position: "absolute",
                right: 92,
                top: 134,
                opacity: tp * 0.9,
                fontFamily: EN,
                fontWeight: 600,
                fontSize: 26,
                letterSpacing: 2,
                color: C.muted,
                textTransform: "uppercase",
              }}
            >
              {en}
            </div>
            <div
              style={{
                position: "absolute",
                left: 90,
                top: 60,
                opacity: tp,
                fontFamily: MONO,
                fontSize: 26,
                color: C.muted,
              }}
            >
              <span style={{ color: C.text, fontWeight: 700 }}>{String(index).padStart(2, "0")}</span> /{" "}
              {String(total).padStart(2, "0")}
            </div>
            <div
              style={{
                position: "absolute",
                left: 90,
                top: 104,
                width: 220,
                height: 4,
                borderRadius: 2,
                background: C.line,
              }}
            >
              <div
                style={{
                  width: `${(index / total) * 100}%`,
                  height: "100%",
                  borderRadius: 2,
                  background: `linear-gradient(90deg, ${C.attn}, ${C.hot})`,
                }}
              />
            </div>
          </>
        )}
        <AbsoluteFill>{children}</AbsoluteFill>
        <Caption t={t} />
        {getInputProps().noAudio ? null : (
          <Sequence from={Math.round(LEAD * fps)} layout="none">
            <Audio src={staticFile(t.audio)} />
          </Sequence>
        )}
      </AbsoluteFill>
    </Ctx.Provider>
  );
};

/** A row of small tokens (words). */
export const Tokens: React.FC<{
  x: number;
  y: number;
  words: string[];
  p?: (i: number) => number;
  color?: string;
  hi?: (i: number) => number;
  w?: number;
  gap?: number;
  size?: number;
}> = ({ x, y, words, p = () => 1, color = C.muted, hi = () => 0, w = 110, gap = 14, size = 26 }) => (
  <>
    {words.map((word, i) => (
      <div
        key={i}
        style={{
          position: "absolute",
          left: x + i * (w + gap),
          top: y,
          width: w,
          height: 56,
          borderRadius: 12,
          opacity: p(i),
          translate: `0px ${(1 - p(i)) * 20}px`,
          border: `2px solid ${hi(i) > 0.01 ? C.gold : color}`,
          background: hi(i) > 0.01 ? `${C.gold}33` : `${color}1a`,
          boxShadow: `0 0 ${hi(i) * 30}px ${C.gold}88`,
          color: C.text,
          fontFamily: EN,
          fontSize: size,
          fontWeight: 600,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        {word}
      </div>
    ))}
  </>
);

export const Formula: React.FC<{
  x: number;
  y: number;
  p: number;
  size?: number;
  children: React.ReactNode;
  center?: boolean;
  w?: number;
}> = ({ x, y, p, size = 44, children, center, w }) => (
  <div
    style={{
      position: "absolute",
      left: x,
      top: y,
      width: w,
      textAlign: center ? "center" : "left",
      opacity: p,
      translate: `0px ${(1 - p) * 20}px`,
      fontFamily: MONO,
      fontSize: size,
      fontWeight: 500,
      color: C.text,
      whiteSpace: "nowrap",
    }}
  >
    {children}
  </div>
);

/** Small colored "cell" grid used for attention matrices. */
export const Matrix: React.FC<{
  x: number;
  y: number;
  n: number;
  cell: number;
  value: (r: number, c: number) => number; // 0..1 intensity, <0 = hidden
  color: string;
  p?: number;
}> = ({ x, y, n, cell, value, color, p = 1 }) => {
  const cells: React.ReactNode[] = [];
  for (let r = 0; r < n; r++) {
    for (let c = 0; c < n; c++) {
      const v = value(r, c);
      cells.push(
        <div
          key={`${r}-${c}`}
          style={{
            position: "absolute",
            left: c * cell,
            top: r * cell,
            width: cell - 3,
            height: cell - 3,
            borderRadius: Math.max(2, cell * 0.12),
            background: v < 0 ? `${C.line}55` : color,
            opacity: v < 0 ? 0.6 : 0.12 + v * 0.88,
          }}
        />,
      );
    }
  }
  return (
    <div style={{ position: "absolute", left: x, top: y, width: n * cell, height: n * cell, opacity: p }}>
      {cells}
    </div>
  );
};

/** Deterministic pseudo random in [0,1). */
export const rand = (i: number) => {
  const s = Math.sin(i * 12.9898 + 78.233) * 43758.5453;
  return s - Math.floor(s);
};
