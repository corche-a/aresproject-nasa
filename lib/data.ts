import { promises as fs } from "node:fs";
import path from "node:path";
import type { AnalogsData, BasinRecord } from "./types";

export async function getData(): Promise<AnalogsData> {
  const file = path.join(process.cwd(), "public", "data", "analogs_data.json");
  return JSON.parse(await fs.readFile(file, "utf8")) as AnalogsData;
}
export async function getBasin(id: string): Promise<BasinRecord[]> {
  const data = await getData();
  return data.records.filter((record) => record.basin_id === id);
}
