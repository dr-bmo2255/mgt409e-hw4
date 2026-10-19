# Ask Dan Image Studio

A local, human-supervised studio for creating the **catalogue-scoped Handsome Dan images** for the Campus Customs store:
inventory → generate → review (approve / revise / reject) → export. It never spends money without your explicit authorization.

## Launch (Mac)
> **Graders:** the dashboard is pre-built and the studio starts in free **Mock mode**, so you can walk through the whole workflow with no API key. Run `cd backend && uv sync`, then the command below. The course input zips, run state and full-size outputs aren't in the repo; the asset plan (`manifest/`) and references are.

- Double-click **`start.command`**, or run:
  ```bash
  cd ask-dan-image-studio/backend && .venv/bin/uvicorn app:app --host 127.0.0.1 --port 8765
  ```
- Open **http://127.0.0.1:8765** (localhost only).
- First-time setup: `cd backend && uv sync` then `cd ../frontend && npm install && npm run build`.

## Inputs (`input/`, never modified)
`ASK_DAN_CLAUDE_CODE_IMAGE_STUDIO_SPEC.txt`, `Dan Final Images(2).zip`, `Dan Image References.zip`
(labeled shield screenshots + Welcome Dan), `data 2.zip` (catalogue DB + product photos), `ask_dan_data2_audit.xlsx`,
`ask_dan_data2_checklist.txt`. Newer files with the same name pattern are picked up automatically. Then use
**Overview → rebuild** (or `POST /api/inventory/rebuild`). ZIPs are extracted defensively (no zip-slip, bomb limits, macOS junk skipped);
the catalogue DB is opened read-only.

## API key
Put `OPENAI_API_KEY` **or** `PORTKEY_API_KEY` in `ask-dan-image-studio/.env` (see `.env.example`). The studio also reads the
Campus Customs project `.env` two folders up. The key is never shown, logged, or exported. The dashboard only shows "present".

## Spending safeguards
- Provider defaults to **Mock** (free labeled placeholders), which exercises the whole workflow at $0.
- Paid requests need **all** of the following: provider = OpenAI, key present, **Dan references confirmed**, an **active authorization**
  naming the asset (pilot / batch / single), the **hard cumulative cap**, the **per-image cap**, and the **max attempts** limit.
  These are checked when queued and again right before sending.
- **Phase 1 pilot:** exactly 3 images (`dan_school_management`, `dan_sport_lacrosse`, `dan_hoodie`), then it stops.
  **Phase 2:** supervised batches of 1–5, only after all 3 pilot images are reviewed. **Automatic mode** is locked off.
- If the app stops mid-request, the job is marked *failed (interrupted)* and is **never silently re-sent**. A file saved just before a crash is recovered, not regenerated.
- Cost is computed from the provider's reported token usage when present, and otherwise labeled *estimated* (official token prices: image in $8/1M, image out $30/1M, text $5/1M).

## Workflow
1. **Overview:** reconciled counts vs. the previous audit, budget, cost estimates, activity.
2. **Settings:** pick and **confirm** Dan references (original "Dan" images only, never Dan2), check the 31 cropped shields, choose provider, size and quality, set caps.
3. **Batch control → Run pilot.**
4. **Generate / Review:** large image, version strip and side-by-side compare, references, prompt. **Approve**, **Revise with feedback**
   (the current image is sent back as an edit reference), **Reject** (reason saved), **Next / Previous**.
   **Place exact supplied shield:** drag sliders to composite the official shield pixels onto the garment as a new free version.
5. **🐶 Ask Dan chat (one-off images):** describe any Dan image, even one the catalogue doesn't need yet. A PydanticAI agent
   (class Portkey key, text only) drafts an editable brief: setting, outfit, pose, humor, exact allowed text, and an official shield
   chosen only from the supplied set. **Create & generate** registers it as a `dan_custom_*` asset and generates through the same
   guarded pipeline (paid: cost shown, one-image authorization). Ask for changes ("make this one nighttime") and the agent proposes a
   precise revision, using the current image as the edit reference. One-offs never change the 35-asset catalogue scope. They're reviewed
   in Generate / Review and exported to `custom_png/`.
6. **Export:** ZIP of approved PNGs, mapping JSON/CSV, refreshed XLSX/TXT, and a review & cost report.

## Folders
`references/dan` (identity refs) · `references/shields` (exact heraldry) · `manifest/assets.json` · `state/studio.sqlite` ·
`output/pending_review | approved (+versions/) | rejected | exports` · `reports/inventory_report.md`.

## Tests
`cd backend && uv run pytest`: 31 tests covering safe ZIPs, mapping, the status machine, mock end to end, paid guards with a fake transport
(real network is blocked in tests), the pilot stop, the spend cap, resume without duplicates, and exports.

## Troubleshooting
- *"No active authorization"*: authorize the pilot or a batch in Batch control, or accept the one-image prompt in Review.
- *Shield wrong in a generated image*: use **Place exact supplied shield**, or revise with feedback.
- *Port in use*: change `--port` in `start.command`.
