import { readFile } from "node:fs/promises";
import path from "node:path";

export async function loadPaperFocus(
  focusDir: string | null | undefined,
  pdfPath: string,
): Promise<string | null> {
  if (!focusDir) {
    return null;
  }

  const focusPath = path.join(focusDir, `${path.basename(pdfPath, path.extname(pdfPath))}.txt`);
  try {
    const focus = (await readFile(focusPath, "utf8")).trim();
    return focus.length > 0 ? focus : null;
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === "ENOENT") {
      return null;
    }
    throw error;
  }
}
