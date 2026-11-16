import type { Target } from "./types";

const targetDescriptions: Record<string, string> = {
  jezero_mars: "Ancient paleolake and delta with lacustrine carbonates, smectite clays, and fluvial fans.",
  gale_mars: "Closed basin with sulfate strata, lacustrine mudstones, and high aeolian activity.",
  meridiani_mars: "Evaporitic plain rich in sulfates such as jarosite and gypsum, with nearly flat terrain.",
  eberswalde_mars: "Endorheic basin with phyllosilicate deposits and a well-preserved inverted delta.",
  lunar_south_pole: "Hyper-arid environment without an atmosphere, extreme thermal shock, and fine abrasive dust.",
};

export function targetDescription(target: Target): string {
  return targetDescriptions[target.id] ?? target.description;
}
