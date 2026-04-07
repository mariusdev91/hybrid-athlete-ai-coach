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
      plannedDate: item.planned_date || null,
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

export function buildPlanDateIndex(plan) {
  if (!plan?.items?.length) {
    return {};
  }

  const sessions = {};

  for (const item of plan.items) {
    const plannedDate = item.planned_date || buildFallbackDateKey(plan?.start_date, item.week_index, item.day_index);
    const key = plannedDate || `${item.week_index || 1}-${item.day_index || 1}`;
    const existing = sessions[key] || {
      key,
      isoDate: plannedDate || null,
      weekIndex: item.week_index || 1,
      dayIndex: item.day_index || 1,
      sessionLabel: item.session_label || `Day ${item.day_index || 1}`,
      sessionFocus: item.session_focus || item.phase_name || "General session",
      phaseName: item.phase_name || "Training Day",
      items: [],
    };

    existing.items.push(item);
    sessions[key] = existing;
  }

  return sessions;
}

export function buildPlanSessions(plan) {
  return Object.values(buildPlanDateIndex(plan)).sort((left, right) => {
    if (left.isoDate && right.isoDate) {
      return left.isoDate.localeCompare(right.isoDate);
    }
    if (left.weekIndex !== right.weekIndex) {
      return left.weekIndex - right.weekIndex;
    }
    return left.dayIndex - right.dayIndex;
  });
}

export function buildCurrentMonthCalendar(plan, referenceDate = new Date()) {
  const dateIndex = buildPlanDateIndex(plan);
  const cursor = new Date(referenceDate);
  const monthStart = new Date(cursor.getFullYear(), cursor.getMonth(), 1);
  const monthEnd = new Date(cursor.getFullYear(), cursor.getMonth() + 1, 0);
  const startOffset = (monthStart.getDay() + 6) % 7;
  const gridStart = new Date(monthStart);
  gridStart.setDate(monthStart.getDate() - startOffset);
  const todayKey = toIsoDate(new Date());
  const weeks = [];
  let activeDate = new Date(gridStart);

  for (let weekIndex = 0; weekIndex < 6; weekIndex += 1) {
    const days = [];

    for (let dayIndex = 0; dayIndex < 7; dayIndex += 1) {
      const isoDate = toIsoDate(activeDate);
      days.push({
        key: isoDate,
        isoDate,
        dayNumber: activeDate.getDate(),
        inCurrentMonth: activeDate.getMonth() === monthStart.getMonth(),
        isToday: isoDate === todayKey,
        session: dateIndex[isoDate] || null,
      });
      activeDate = addDays(activeDate, 1);
    }

    weeks.push(days);
  }

  return {
    monthLabel: new Intl.DateTimeFormat("en-GB", {
      month: "long",
      year: "numeric",
    }).format(monthStart),
    weekdayLabels: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
    todayKey,
    totalScheduledDays: Object.values(dateIndex).filter((session) => {
      if (!session.isoDate) {
        return false;
      }
      return session.isoDate >= toIsoDate(monthStart) && session.isoDate <= toIsoDate(monthEnd);
    }).length,
    weeks,
  };
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
  const sessions = buildPlanSessions(plan);
  return {
    totalWeeks: weeks.length,
    totalSessions: sessions.length,
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

function buildFallbackDateKey(startDate, weekIndex, dayIndex) {
  if (!startDate) {
    return null;
  }

  const start = new Date(startDate);
  if (Number.isNaN(start.getTime())) {
    return null;
  }

  return toIsoDate(addDays(start, ((weekIndex || 1) - 1) * 7 + ((dayIndex || 1) - 1)));
}

function addDays(value, amount) {
  const copy = new Date(value);
  copy.setDate(copy.getDate() + amount);
  return copy;
}

function toIsoDate(value) {
  return new Date(value.getTime() - value.getTimezoneOffset() * 60000).toISOString().slice(0, 10);
}
