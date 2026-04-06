export function buildPlanCalendar(plan) {
  if (!plan?.items?.length) {
    return [];
  }

  const weeks = new Map();

  for (const item of plan.items) {
    const weekIndex = item.week_index || 1;
    const dayIndex = item.day_index || 1;
    const week = weeks.get(weekIndex) || {
      weekIndex,
      phaseName: item.phase_name || "Training Week",
      days: new Map(),
    };
    const dayKey = String(dayIndex);
    const day = week.days.get(dayKey) || {
      key: `${weekIndex}-${dayIndex}`,
      weekIndex,
      dayIndex,
      sessionLabel: item.session_label || `Day ${dayIndex}`,
      sessionFocus: item.session_focus || item.phase_name || "General session",
      phaseName: item.phase_name || "Training Week",
      items: [],
    };

    day.items.push(item);
    week.days.set(dayKey, day);
    weeks.set(weekIndex, week);
  }

  return Array.from(weeks.values())
    .sort((left, right) => left.weekIndex - right.weekIndex)
    .map((week) => ({
      ...week,
      days: Array.from(week.days.values()).sort((left, right) => left.dayIndex - right.dayIndex),
    }));
}

export function getSessionSummary(session) {
  if (!session) {
    return [];
  }

  return [
    `Phase: ${session.phaseName || "n/a"}`,
    `Focus: ${session.sessionFocus || "n/a"}`,
    `Movements: ${session.items.length}`,
  ];
}

export function getPlanOverview(plan) {
  const weeks = buildPlanCalendar(plan);
  return {
    totalWeeks: weeks.length,
    totalSessions: weeks.reduce((total, week) => total + week.days.length, 0),
    totalExercises: plan?.items?.length || 0,
  };
}

export function slugify(value) {
  return String(value || "workout-plan")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 60);
}
