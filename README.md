# RealtorBot

A LINE assistant for Thai real estate agents. Agents type in everyday Thai, the way they already chat, and the bot files properties, clients, follow-ups and photos for them. There's no app to install and no forms to fill in.

This is a working prototype, built and tested end to end from a real LINE account in October 2026.

## What it does today

| The agent types in LINE | What the bot does |
|---|---|
| `เพิ่มทรัพย์ Lumière ย่านอโศก ราคา 8900000` | Adds a new property and replies with a summary |
| `The Line Jatujak 120 ตร.ม.` | Updates the existing property instead of creating a duplicate |
| `Lumière ราคาเท่าไร` | Looks up the property and replies with its price and status |
| `คุณสมชายนัดดูห้อง Lumière` | Creates or updates the client, sets the stage to *Viewing*, links the property |
| `ใครต้อง follow up วันนี้` | Lists the clients whose follow-up date is due |
| *(sends 3 photos)*, then the property name | Stores the photos in that property's own Google Drive folder |

- **Thai natural language:** Claude (Haiku 4.5) turns each message into a structured intent: `add_property`, `ask_price`, `search_property`, `update_client`, `set_followup`, `list_followups`, or `unknown`.
- **Conversation memory:** the user's last 6 messages are passed as context. "เพิ่ม 3 ห้องนอน" therefore applies to the property that was just discussed.
- **Asks instead of guessing:** when details are missing, it asks a short question back and never invents numbers. Relative dates such as "พรุ่งนี้" and "วันศุกร์" are resolved to real dates.
- **Unit numbers:** `The Line Jatujak ห้อง 1204` is stored as the unit `The Line Jatujak #1204`.
- **Photo folders per property:**
  1. The first photo creates a `draft` folder.
  2. Naming the property renames that folder to `P-<id> <name>`.
  3. Photos added to an existing property later go into a dated `รูปเพิ่ม …` subfolder inside it.
  4. Every photo link is written to the property's row.
- **Client pipeline:** Inquiry → Viewing → Offer → Negotiation → Contract → Transfer.
- **Audit log:** every message is logged with the raw text and the parsed JSON, so mistakes can be reviewed.

## Architecture

```
LINE Messaging API ──webhook──▶ Make.com scenario (62 modules)
                                   ├─ text  ─▶ Claude API (intent + fields as JSON)
                                   │           └─▶ Google Sheets: Properties / Clients / Log
                                   └─ image ─▶ LINE content API ─▶ Google Drive (folder per property)
                                ◀── reply via LINE ──┘
```

Google Sheets is the database. It's deliberately simple, and the agent can open and correct it by hand.

## Repository layout

| File | Purpose |
|---|---|
| `build_scenario_a.py` | **The source of truth.** Generates the whole Make scenario as code: routing, filters, Sheets and Drive steps, the Claude prompt, LINE replies and error handlers. |
| `scenario_a_blueprint.json` | The generated Make blueprint, exactly as deployed. |

```bash
python build_scenario_a.py   # writes scenario_a_blueprint.json
```

The blueprint is then imported or updated in Make. It references the Make connection IDs and the Google Sheet and Drive folder of the original account. To run it elsewhere, replace the constants at the top of `build_scenario_a.py` with your own.

## How it was built

The scenario is written as code instead of being wired by hand in the Make editor. The whole bot can then be regenerated, reviewed and redeployed in one step.

It was built mostly with an AI coding agent (Claude Code), using this loop:
1. Generate the blueprint from `build_scenario_a.py`.
2. Deploy it to Make through the Make API.
3. Run a real test from LINE.
4. Have the agent read the Make execution history and check the actual result in Google Drive and Sheets.
5. Find the root cause, fix the generator, redeploy, and test again.

Two bugs caught this way:
- Uploaded photos were named `xxx.jpg.jpg`. The Drive module appends the extension to the title, so the title now has no extension.
- A text-only update to an existing property wiped its photo links and folder ID. A mapped expression that evaluates to an empty string clears the cell, so the update now always writes back the merged value.

## Roadmap

These are not built yet:
- **Buyer–listing matching:** store each buyer's must-haves and alert the agent when a new listing matches.
- **Drafted follow-ups** after a showing, in the agent's own voice.
- **Pre-showing brief:** the client's history and the points already negotiated.
- **Proactive morning reminders** instead of on-demand lists.
- **Shared knowledge for agent teams.**
