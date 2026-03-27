# PDF Annotation Tool

A tool that reads a PDF file and a set of rules written in YAML, then places visual marks (ticks, flags, arrows, badges) directly on the PDF. Results can be produced via a command-line interface (CLI) or through a browser-based REST API.

---

## What it does

You describe *what to mark* and *how to mark it* in a simple YAML file. The tool searches the PDF for the text you specified and places the chosen mark next to every match it finds. After saving the annotated PDF, it verifies that every rule produced at least one annotation and reports a PASS/FAIL summary.

### Available mark types

| Type | Description |
|---|---|
| `tick` | Green tick mark (✓) |
| `flag` | Red flag (⚑) |
| `back_reference` | Blue back-reference arrow (←) |
| `paragraph_end` | Green paragraph-end slash (/) |
| `badge` | Text badge computed by a plugin (e.g. "GP 40%") |
| `shading_badge` | Coloured shaded badge with static text |

### Available positions

`right`, `left`, `above`, `below`, `flush_right`

---

## Technical implementation

Two requirements that previous implementations commonly get wrong — this tool addresses both explicitly.

**`add_freetext_annot()`**
All marks (ticks, flags, arrows, badges, shading badges) are placed using PyMuPDF's `page.add_freetext_annot()`. This writes a proper PDF FreeText annotation object — not a drawing or an image overlay — which means annotations are selectable, searchable, and handled correctly by PDF viewers and downstream processing tools. See `src/pdf_annotation_tool/mark_placer.py`.

**Incremental save**
After annotations are written, the file is saved using `doc.save(output_path, incremental=True, encryption=fitz.PDF_ENCRYPT_KEEP)`. Incremental save appends changes to the end of the PDF without rewriting or reparsing the original content. This preserves the document's internal structure, existing metadata, and any security settings — the original bytes are never touched. See `src/pdf_annotation_tool/service.py`.

---

## Prerequisites

You need two tools installed on your machine before starting:

- **Python 3.12 or newer** — download from [python.org](https://www.python.org/downloads/)
- **uv** — a fast Python package manager

Install `uv` by running this in your terminal:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

> **Windows users:** use the PowerShell installer shown on the [uv documentation page](https://docs.astral.sh/uv/getting-started/installation/).

---

## Setup (do this once)

Open a terminal, navigate to the project folder, and run:

```bash
uv sync
```

This downloads all required packages into an isolated environment. You do not need to activate a virtual environment — all subsequent commands use `uv run` which handles that automatically.

---

## Running the tests

```bash
uv run pytest tests/
```

A passing run looks like:

```
collected 30 items

tests/test_api.py ............
tests/test_cli.py ....
...
30 passed in 3.21s
```

To see more detail (which test did what):

```bash
uv run pytest tests/ -v
```

---

## Sample files

The `samples/` directory contains three ready-to-use PDF files and a rules file:

| File | Description |
|---|---|
| `samples/income_statement.pdf` | Sample income statement PDF |
| `samples/balance_sheet.pdf` | Sample balance sheet PDF |
| `samples/cash_flow.pdf` | Sample cash flow statement PDF |
| `samples/rules.yaml` | Example rules file with tick, flag, arrow, and paragraph-end marks |

---

## CLI — using the tool from the terminal

The CLI takes an input PDF, a rules YAML file, and an output path.

**Basic usage:**

```bash
uv run python -m src.cli <input_pdf> <rules_yaml> -o <output_pdf>
```

**Example using the included sample files:**

```bash
uv run python -m src.cli samples/income_statement.pdf samples/rules.yaml -o output.pdf
```

**What you will see:**

```
Annotated PDF saved to: output.pdf
Marks placed: 9

Verification results:
  Rule                                     Status Annotations
  ---------------------------------------- ------ -----------
  Tick Total Revenue                       PASS   2
  Tick Gross Profit First                  PASS   1
  Flag Net Income                          PASS   3
  Flag Total Equity Page 1                 PASS   1
  Ref Cash Flow                            PASS   1
  Para End Period                          PASS   1

Overall: PASS (9 total annotations)
```

The file `output.pdf` is saved in the current folder. Open it with any PDF viewer to see the marks placed on the document.

**Exit codes:** `0` = all rules passed, `1` = one or more rules failed (useful for scripting).

---

## UI — using the browser interface

### Step 1 — Start the server

```bash
uv run uvicorn src.api:app --reload
```

You will see output like:

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
```

Leave this terminal open while you use the UI. To stop the server press `CTRL+C`.

### Step 2 — Open the interactive docs

Open your browser and go to:

```
http://localhost:8000/docs
```

You will see the Swagger UI — an interactive page listing all available API endpoints.

### Step 3 — Annotate a PDF

1. Click on the **POST /annotate** row to expand it.
2. Click the **Try it out** button (top right of that section).
3. Under **pdf_file**, click **Choose File** and select a PDF (e.g. `samples/income_statement.pdf`).
4. Under **rules_file**, click **Choose File** and select a rules YAML (e.g. `samples/rules.yaml`).
5. Click the blue **Execute** button.

The response body will appear below. It contains:
- `job_id` — a unique ID for this annotation job
- `marks_placed` — total number of marks added
- `details` — which rule matched on which page
- `verification` — PASS/FAIL per rule

**Example response:**

```json
{
  "job_id": "a1b2c3d4-...",
  "marks_placed": 9,
  "details": [
    { "rule": "Tick Total Revenue", "page": 0, "rect": [...] },
    ...
  ],
  "verification": {
    "passed": true,
    "total_annotations": 9,
    "rule_results": [
      { "rule_name": "Tick Total Revenue", "status": "PASS", "annotations_found": 2 },
      ...
    ]
  }
}
```

### Step 4 — Download the annotated PDF

1. Copy the `job_id` value from the response (without the quotes).
2. Scroll up and click on the **GET /download/{job_id}** row to expand it.
3. Click **Try it out**.
4. Paste the `job_id` into the `job_id` field.
5. Click **Execute**.
6. Click the **Download file** link that appears in the response to save `annotated.pdf`.

Open the downloaded PDF in any PDF viewer to see the annotations.

---

## Rules file format

Rules are written in YAML. Each rule specifies what text to search for and what mark to place.

```yaml
rules:
  # Place a green tick to the right of every occurrence of "Total Revenue"
  - name: "Tick Total Revenue"
    type: tick
    search: "Total Revenue"
    position: right
    match: all

  # Place a red flag above the first occurrence of "Gross Profit" only
  - name: "Flag Gross Profit First"
    type: flag
    search: "Gross Profit"
    position: above
    match: first

  # Place a red flag below "Total Equity" but only on page 1
  - name: "Flag Total Equity Page 1"
    type: flag
    search: "Total Equity"
    position: below
    match: "page:1"

  # Place a blue back-reference arrow with a small horizontal offset
  - name: "Ref Cash Flow"
    type: back_reference
    search: "Cash Flow"
    position: right
    match: all
    offset_x: 2.0
```

### Rule fields

| Field | Required | Description |
|---|---|---|
| `name` | Yes | Unique name for the rule (shown in verification output) |
| `type` | Yes | Mark type: `tick`, `flag`, `back_reference`, `paragraph_end`, `shading_badge` |
| `search` | Yes | Text to search for in the PDF |
| `position` | Yes | Where to place the mark: `right`, `left`, `above`, `below`, `flush_right` |
| `match` | No | `all` (default), `first`, or `"page:N"` (1-indexed page number) |
| `offset_x` | No | Fine-tune horizontal position in points |
| `offset_y` | No | Fine-tune vertical position in points |
| `fill_color` | For `shading_badge` | Background colour: `amber`, `red`, or `yellow` |
| `badge_text` | For `shading_badge` | Text displayed inside the badge |
| `plugin` | For computed badges | Plugin name (e.g. `gp_percentage`) for calculated values |
