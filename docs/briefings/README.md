# JB Lines Briefing Routine Prompts — Employee Hours Flagging

Version-controlled replacement prompts for the cloud Routines (scheduled triggers)
that generate the JB Lines briefings. Each file is the **complete replacement
prompt** for the Routine whose trigger ID is embedded in its filename, built from
the live prompt fetched **Oct 17 2026** plus the Employee Hours Check additions
and nothing else.

## How to apply (Mark — this part is yours)

Agents cannot edit these Routines (they were created from the claude.ai side, and
only their creator can edit them). For each row below: open the link, replace the
prompt with the full contents of the file, and save. Apply all seven — each file
already contains everything the Routine has today (including the Oct 13/16 L10 and
app-data additions), so pasting is a pure upgrade.

| Routine | Edit link | File to paste |
|---|---|---|
| Ben Daily Briefing | https://claude.ai/code/routines/trig_018CWS7uvHSsiG8bmH5qpRFa | `ben-daily-briefing.trig_018CWS7uvHSsiG8bmH5qpRFa.md` |
| Daily CEO Briefing | https://claude.ai/code/routines/trig_013pSqaT2sq2t2mwY57Jv52n | `daily-ceo-briefing.trig_013pSqaT2sq2t2mwY57Jv52n.md` |
| Jenna Daily Briefing | https://claude.ai/code/routines/trig_019R1h8YQ8ryj7E6Cg86zptJ | `jenna-daily-briefing.trig_019R1h8YQ8ryj7E6Cg86zptJ.md` |
| Hyrum Daily Briefing (currently disabled) | https://claude.ai/code/routines/trig_013xYFRhwakspKQPHwfJf5H8 | `hyrum-daily-briefing.trig_013xYFRhwakspKQPHwfJf5H8.md` |
| Santi Morning Briefing | https://claude.ai/code/routines/trig_01HmFxZKUwPQDiTQjbqULKEk | `santi-morning-briefing.trig_01HmFxZKUwPQDiTQjbqULKEk.md` |
| CEO EOD Scoreboard | https://claude.ai/code/routines/trig_01YC5XgS6hQANSk3RdtsAdmZ | `ceo-eod-scoreboard.trig_01YC5XgS6hQANSk3RdtsAdmZ.md` |
| Weekly CEO Review | https://claude.ai/code/routines/trig_01MsPhf8w1WsohXwgAkFDtTD | `weekly-ceo-review.trig_01MsPhf8w1WsohXwgAkFDtTD.md` |

If you changed any of these Routine prompts yourself after Oct 17 2026, don't
paste that file — ask Claude to re-splice the hours block onto your newer text
first, or the paste will undo your change.

## What the hours check adds

- Thresholds: **> 50 hrs/week = OVERWORKED ⚠️**, **< 30 hrs/week = UNDERWORKED**
- Scope: **hourly employees only** — salaried employees are excluded from all
  hours reporting (no flags, no mention, no "no data" lines); pay type comes from
  QuickBooks payroll (`qbo_payroll_get_company_pay_types` /
  `qbo_payroll_get_employee_compensations`)
- Official record: QuickBooks payroll payslips, per pay period (the QuickBooks
  connector has no live timesheet tools, so QB hours arrive on payroll cadence)
- Early warning between payrolls: Samsara GPS on-site hours projected to a weekly
  pace (GPS only sees crew on trucks — a GPS gap is never treated as zero hours)
- Fallback: if QuickBooks is unavailable at run time, sections read
  "Samsara pace only — QB unavailable"
- Privacy: Jenna / Hyrum / Santi versions report hours only — never wages or pay
  amounts. Jazmine's and Darcy's briefings are intentionally excluded and are not
  in this folder.

Per-briefing shape: Ben gets gather step 15 + a HOURS WATCH section (max 5 lines,
"all crew within normal range" when clean, payroll-side closure evidence next to
crew verification); the Daily CEO gets step 1b, exceptions only, TOP 3 eligible;
Jenna (step 10), Hyrum (step 12) and Santi (step 14) get a 3-line-max HOURS WATCH
that is omitted when nobody crosses a threshold; the EOD Scoreboard gets step 7
(same-day Samsara pace) and a single HOURS exceptions line; the Weekly CEO Review
gets step 3b with a per-employee hours table for the last two pay periods plus
week-over-week deltas.
