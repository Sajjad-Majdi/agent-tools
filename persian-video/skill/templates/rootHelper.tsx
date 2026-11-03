import React from "react";
import { Composition } from "remotion";
import timing from "./timing.json";
import { SceneTiming, sceneFrames } from "./kit";
import type { SP } from "./scenes1";

const TIMING = timing as SceneTiming[];

/** Root that registers one `T-<id>` composition per scene, for isolated previews. */
export const makeRoot = (scenes: Record<string, React.FC<SP>>): React.FC => {
  const Root: React.FC = () => (
    <>
      {Object.entries(scenes).map(([id, Scene]) => {
        const i = TIMING.findIndex((t) => t.id === id);
        const t = TIMING[i];
        const C: React.FC = () => <Scene t={t} index={i + 1} total={TIMING.length} />;
        return <Composition key={id} id={`T-${id}`} component={C} durationInFrames={sceneFrames(t, 30)} fps={30} width={1920} height={1080} />;
      })}
    </>
  );
  return Root;
};
