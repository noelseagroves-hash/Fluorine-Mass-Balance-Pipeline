# Working on this project

Notes for Claude. `START_HERE.md` is the equivalent for a lab member running a
batch; read that too, since it describes what the pipeline is for.

## What this is

`TA_Processing.ipynb` implements `TA Code Spec.md`: raw targeted-analysis exports
from an LC-MS in, a censored and QC-assessed PFAS dataset out. Eleven spec
sections, built one at a time.

The notebook's first cell carries a status table saying which sections exist. That
table and `git log` are the source of truth for progress — trust them over anything
written here.

## How Noel wants this built

**One spec section per increment.** Propose the next single section, get approval,
implement it, then show evidence it works on real data — actual row counts,
computed values, named samples — before proposing the next. Do not batch sections.

**Then prompt to update the spec.** Once Noel says a section is good, ask whether
to update `TA Code Spec.md` to match what the code does, naming the specific edits.
Never edit the spec unprompted. This is why the spec still describes the pipeline
accurately rather than drifting from it.

**Compactness is a hard requirement.** An earlier attempt at this project was
abandoned because the code grew too long for Noel to keep a handle on. Keep
processing cells under about 30 lines; when one would outgrow that, factor the
repeated part into a small named helper rather than letting it sprawl. Keep
verification prints in cells separate from processing logic. Report the line count
per section, and flag a section trending long before it becomes a problem.

**Noel is a scientist, not a programmer.** Every section gets a plain-language
markdown cell above it saying what it does and why, in terms a chemist reads.
Prefer explicit visible pandas operations over clever abstractions. Do not let a
Python rule become something Noel has to learn around — `solid`, `liquid` and
`auto` are defined as bare words in §4 precisely so that quoting never matters.

**All logic lives inline in the notebook**, not in an imported package. This was a
deliberate choice, accepting worse pull-request diffs, so that every step is
readable in place.

## The verification loop that matters

Every bug found so far was found by running real data, not by reading code. Two of
them — a pandas `str` dtype that refuses to hold numbers, and instrument blanks
being compared against limits in a different unit — were invisible to inspection
and only appeared when real arithmetic hit real values.

So: implement, run, and read the output before claiming anything works.

The batch lives in `runs/<name>/`, gitignored. Execute it headlessly rather than
asking Noel to run it:

```
cd runs/<name>
jupyter nbconvert --to notebook --execute --allow-errors \
    --output <somewhere-temporary>/run.ipynb TA_Processing.ipynb
```

`--allow-errors` is important: without it nbconvert writes no output notebook when
a cell raises, so you get the traceback but not the prints that led to it. Then
read each cell's `outputs` from that JSON.

Assertions in the check cells have caught several of my own errors. Keep adding
them; they are not decoration.

## Repository layout

- `TA_Processing.ipynb` — the **template**, batch inputs left blank. Never fill it
  in. The first cell prints whether it is the template or a run.
- `runs/<name>/` — a batch, made by `python new_run.py <name>`. Gitignored, along
  with the masses and results inside it. A run belongs to whoever is running that
  batch and is theirs to edit; only changes meant for everyone go in the template.
- `TA Code Spec.md` — the spec of record.
- `docs/superpowers/specs/2026-09-15-ta-processing-design.md` — where the code
  deliberately differs from the spec and why, plus the open questions blocking
  later sections. **Read this before changing anything.**
- `CONTRIBUTING.md` — branch, pull request, review.

## Environment

Miniconda, with packages from **conda-forge using `--override-channels`**. Do not
use Anaconda's default channels: they require accepting terms of service, which is
not Claude's to accept on Noel's behalf. `environment.yml` captures this.

## What only Noel can supply

Some values exist nowhere in the data. Ask rather than infer:

- which samples served as method blanks (§5)
- the spike factor per compound, and the low and high spike amounts in ng (§6)
- the NIS compound list, and the NIS-to-EIS assignments (§7)

The spec calls several of these "hard coded". They are not in the exports, and
guessing them would produce numbers that look plausible and are wrong.
