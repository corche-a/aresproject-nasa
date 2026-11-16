import { getData } from "../../../lib/data";
export async function GET() { return Response.json((await getData()).records); }
