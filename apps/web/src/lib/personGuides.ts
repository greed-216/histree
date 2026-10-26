import records from "../data/person-guides.json";
export const personGuides: Record<
  string,
  {
    kicker: string;
    title: string;
    summary: string;
    path: string;
    linkLabel: string;
  }
> = records;
