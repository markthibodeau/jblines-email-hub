# JB Lines Briefing Routine Prompts

Version-controlled copies of the cloud Routine (scheduled trigger) prompts that
generate the JB Lines daily/weekly briefings. The live prompts are stored
server-side and applied with the Claude Code Remote `update_trigger` tool — each
file here is the **complete replacement prompt** for the trigger ID embedded in
its filename.

## What changed in this revision

Added the **Employee Hours Check** to seven briefings:

- Thresholds: **> 50 hrs/week = OVERWORKED ⚠️**, **< 30 hrs/week = UNDERWORKED**
- Scope: **hourly employees only** — salaried employees are excluded from all
  hours reporting (no flags, no mention, no "no data" lines)
- Official record: QuickBooks payroll payslips (per pay period, after each
  payroll run — the QuickBooks connector has no live timesheet tools)
- Early warning between payrolls: Samsara GPS on-site hours projected to a
  weekly pace (GPS only sees crew on trucks — a GPS gap is never treated as
  zero hours)
- Fallback: if QuickBooks is unavailable, sections are labeled
  "Samsara pace only — QB unavailable"
- Privacy: Jenna / Hyrum / Santi versions report hours only — never wages or
  pay amounts. Jazmine's and Darcy's briefings are intentionally excluded
  (external recipients / no-payroll-content rules) and are not in this folder.

| File | Routine | Hours integration |
|---|---|---|
| `ben-daily-briefing.*` | Ben Daily Briefing | Gather step 12 + HOURS WATCH section (cap-exempt); QB hours as payroll-side closure evidence next to crew verification |
| `daily-ceo-briefing.*` | Daily CEO Briefing | Step 1b exception-only rollup, TOP 3 eligible |
| `jenna-daily-briefing.*` | Jenna Daily Briefing | Step 9 + HOURS WATCH; hours only, schedule-rebalancing focus |
| `hyrum-daily-briefing.*` | Hyrum Daily Briefing | Step 10 + HOURS WATCH; crew-planning focus |
| `santi-morning-briefing.*` | Santi Morning Briefing | Step 11 + HOURS WATCH; no dollars (no-finance rule) |
| `ceo-eod-scoreboard.*` | CEO EOD Scoreboard | Evidence step 6 (same-day Samsara pace) + single HOURS exceptions line |
| `weekly-ceo-review.*` | Weekly CEO Review | Step 3b: last-two-pay-periods hours table with deltas + Samsara forward pace |

## Applying a prompt to the live Routine

From a session with Claude Code Remote trigger tools approved:

```
update_trigger(trigger_id: "<id from the filename>", prompt: "<full file contents>")
```

The prompt is replaced in full — always apply the entire file, never a fragment.
