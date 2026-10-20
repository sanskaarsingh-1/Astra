# 📂 Reports — Saved Investigation Reports

Save all exported investigation reports here after live testing.

---

## Naming Convention

```
{date}_{mode}_{scene}_{format}.{ext}

Examples:
  2026-09-21_mode1_urban_ahmedabad_report.md
  2026-09-21_mode2_levir_change_report.html
  2026-09-21_mode3_s1s2_conflict_report.json
```

---

## Report Formats Available

| Format | Button on Website | File Extension | Best For |
|:---|:---|:---|:---|
| Markdown | "Download .md" | `.md` | Reading in VS Code, sharing as text |
| HTML | "Download .html" | `.html` | Printing, sharing as styled document |
| JSON | "Download .json" | `.json` | Programmatic audit, checking DETERMINISTIC tags |

---

## What a Good Report Contains

When you open a downloaded JSON report, verify it has these keys:

```json
{
  "report": "...",
  "evidence": [
    {
      "tool_id": "area-calculator",
      "calculation_status": "DETERMINISTIC",
      "value_m2": 12400.0,
      "value_ha": 1.24
    }
  ],
  "trace": [
    {
      "step_id": "...",
      "tool_id": "...",
      "duration_ms": 234
    }
  ]
}
```

> ✅ `calculation_status: "DETERMINISTIC"` must appear on all spatial measurements (area, distance, NDVI).  
> ❌ If a spatial value has no `calculation_status`, that is a bug — log it in `checklists/TEST_LOG.md`.
