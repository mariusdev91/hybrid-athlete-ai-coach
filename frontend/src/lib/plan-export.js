import * as XLSX from "xlsx";
import { buildPlanCalendar, slugify } from "./plan-utils.js";

export function downloadPlanWorkbook(plan) {
  const weeks = buildPlanCalendar(plan);
  const workbook = XLSX.utils.book_new();

  for (const week of weeks) {
    const rows = [];

    for (const session of week.days) {
      rows.push({
        Date: session.plannedDate || "",
        Session: `${session.sessionLabel} (Day ${session.dayIndex})`,
        Phase: session.phaseName,
        Focus: session.sessionFocus,
        Exercise: "",
        Sets: "",
        Reps: "",
        RestSeconds: "",
        TargetRPE: "",
        Notes: "",
      });

      for (const item of session.items) {
        rows.push({
          Date: item.planned_date || session.plannedDate || "",
          Session: "",
          Phase: "",
          Focus: "",
          Exercise: item.exercise_name,
          Sets: item.prescribed_sets || "",
          Reps: item.prescribed_reps || "",
          RestSeconds: item.rest_seconds || "",
          TargetRPE: item.target_rpe || "",
          Notes: item.notes || "",
        });
      }

      rows.push({
        Date: "",
        Session: "",
        Phase: "",
        Focus: "",
        Exercise: "",
        Sets: "",
        Reps: "",
        RestSeconds: "",
        TargetRPE: "",
        Notes: "",
      });
    }

    const sheet = XLSX.utils.json_to_sheet(rows);
    const sheetName = `Week ${week.weekIndex}`.slice(0, 31);
    XLSX.utils.book_append_sheet(workbook, sheet, sheetName);
  }

  const fileName = `${slugify(plan?.title || "periodized-workout-plan")}.xlsx`;
  XLSX.writeFile(workbook, fileName);
}
