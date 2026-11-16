export interface RosterPerson {
  org: string;
  name: string;
}

/** 一行一人「单位 姓名」；只在最后一个空白处切，单位名里的空格得以保留。 */
export function parseRoster(text: string): RosterPerson[] {
  return text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const match = /^(.*\S)\s+(\S+)$/.exec(line);
      return match ? { org: match[1]!, name: match[2]! } : { org: "", name: line };
    });
}
