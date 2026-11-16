import { getData } from "../../lib/data";
import ExplorerClient from "../../components/ExplorerClient";

export default async function Explorer() {
  return <main className="shell"><ExplorerClient data={await getData()} /></main>;
}
