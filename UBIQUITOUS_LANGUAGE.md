# Ubiquitous Language

## PDF Processing

| Term | Definition | Aliases to avoid |
|------|-----------|-----------------|
| **Annotation** | A visual mark placed on a PDF page as a separate layer on top of the page content | Mark (when referring to the PDF object), overlay |
| **Bounding Box** | The rectangular coordinates (x, y, width, height) that define where a text element exists on a PDF page | Text rect, text position, coordinates |
| **Freetext Annotation** | A PyMuPDF annotation object created via `add_freetext_annot()` that supports Unicode rendering | Freetext annot |
| **Incremental Save** | A PDF save method that appends changes without rewriting the original file, preserving coordinate system integrity | Append save |
| **Content Stream** | The internal PDF layer where `insert_text()` writes — does NOT support Unicode symbols reliably | Page content |

## Annotation Engine

| Term | Definition | Aliases to avoid |
|------|-----------|-----------------|
| **Rule** | A declarative instruction (defined in YAML) that maps a text search to a mark placement | Check, instruction, annotation spec |
| **Rule Engine** | The system that loads rules from YAML config, evaluates them against a PDF, and produces annotations | Rule processor, checker |
| **Mark** | A specific visual symbol (tick, flag, badge, etc.) placed at a computed position relative to found text | Annotation (when referring to the logical concept), symbol |
| **Mark Type** | A category of mark with a defined symbol, color, and default positioning behavior | Annotation type |
| **Text Search** | The process of locating a text string on a PDF page and obtaining its bounding box — the core positioning mechanism | Text matching, text lookup |
| **Match Mode** | The strategy for handling multiple occurrences of searched text: `"all"`, `"first"`, or `"page:N"` | Match strategy |
| **Position** | The spatial relationship between a mark and its target text: `"right"`, `"left"`, `"above"`, `"below"`, or `"flush_right"` | Placement, alignment |
| **Plugin** | A pure Python function auto-discovered from the `plugins/` directory that computes dynamic mark content (text, color) without touching PyMuPDF | Computed rule, calculator |
| **Plugin Result** | The return value of a plugin function containing computed text, color, and mark type — no rendering logic | Plugin output |

## Mark Types

| Term | Definition | Aliases to avoid |
|------|-----------|-----------------|
| **Tick** | A green checkmark (✓) placed after figures and labels to indicate verification | Checkmark, check |
| **Flag** | A red flag symbol (⚑) placed beside exceptions and warnings | Warning mark, alert |
| **Back-Reference** | A blue arrow (←) placed at secondary locations pointing back to a primary annotation | Cross-reference, backref |
| **Paragraph End Mark** | A green slash (/) placed flush against a full stop to mark paragraph completion | End mark, period mark |
| **Badge** | A computed annotation with dynamic text content (e.g. "GP 42%") produced by a plugin | Computed mark, label |
| **Shading Badge** | A colour-coded background annotation indicating status (amber, red, yellow) | Colour badge, status badge |

## System Layers

| Term | Definition | Aliases to avoid |
|------|-----------|-----------------|
| **Service Layer** | The `annotate_pdf()` function that orchestrates the full pipeline and returns an `AnnotationResult` — the integration point for both CLI and API | Orchestrator, controller |
| **Annotation Result** | The return value of the service layer containing statistics (marks placed, rules matched/unmatched) and verification outcome | Result, output, report |
| **Verification Block** | A post-save step that reopens the output PDF and confirms each rule produced at least one annotation, reporting pass/fail per rule | Validator, checker |
| **Sample PDF Generator** | A script that creates test PDFs with varied layouts using PyMuPDF to prove the tool generalizes across different documents | Test PDF creator |

## Relationships

- A **Rule** specifies a **Text Search**, a **Mark Type**, a **Position**, and a **Match Mode**
- A **Rule** may optionally reference a **Plugin** for computed content
- A **Plugin** returns a **Plugin Result** that the **Rule Engine** uses to create a **Mark**
- The **Rule Engine** processes all **Rules** against a PDF and produces **Annotations** via **Freetext Annotations**
- The **Service Layer** calls the **Rule Engine**, performs **Incremental Save**, then runs the **Verification Block**
- The **Verification Block** produces an **Annotation Result** with per-rule pass/fail status
- A **Badge** is a **Mark** whose content is dynamically computed by a **Plugin**

## Example dialogue

> **Dev:** "When the **Rule Engine** processes a **Rule**, does it create the **Annotation** immediately?"
> **Domain expert:** "Yes — for each **Rule**, it runs the **Text Search**, gets the **Bounding Box**, then creates a **Freetext Annotation** at the computed **Position**. If the **Rule** has a **Plugin**, it calls the plugin first to get the **Plugin Result**."
> **Dev:** "What if the **Text Search** finds nothing — the text isn't in the PDF?"
> **Domain expert:** "The **Rule Engine** logs a warning and continues to the next **Rule**. The **Verification Block** will report that rule as unmatched in the **Annotation Result**."
> **Dev:** "And the **Verification Block** — it reopens the saved file?"
> **Domain expert:** "Exactly. After **Incremental Save**, it reopens the output PDF and checks that each **Rule** has at least one **Annotation**. It doesn't re-run the **Text Search** — it just counts annotations per rule. The **Annotation Result** shows pass/fail for every **Rule**."

## Flagged ambiguities

- **"Annotation"** vs **"Mark"**: In our conversation, these were used interchangeably. Resolved: **Mark** is the logical concept (a tick, flag, or badge the user wants placed), while **Annotation** is the PDF object that renders it. A **Mark** becomes an **Annotation** when written to the PDF.
- **"Rule"** vs **"Check"**: The Upwork job posting uses "check" (39 checks, 12 rules). In our design, everything is a **Rule** — the YAML config defines rules, not checks. Avoid "check" to prevent confusion with the **Verification Block**.
- **"Plugin"** vs **"Computed rule"**: A plugin is not a rule — it's a function that a rule *references*. The rule defines what to search for and where to place; the plugin defines what content to show.
