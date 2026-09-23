# Working on this project

> ## ⚠️ READ THIS FIRST — §6 IS NOT SIGNED OFF
>
> **Before proposing §7 or anything else, tell Noel that §6 spike recovery is
> still waiting on their check of the spike calculations.** Do not treat §6 as
> finished and do not start the next section until they have confirmed it.
>
> Left open at the end of the 2026-09-22 session:
>
> 1. **Noel has not yet checked the §6 spike calculations.** The code is
>    verified — assertions pass, and PFOS Oyster low was re-derived by hand from
>    the raw CSV to 92.0%. What is unverified is the *chemistry*: whether the
>    nominal concentrations, the background subtraction and the resulting
>    recoveries are right. Start the session here.
> 2. **34 of 180 recoveries are flagged** outside the 70–130% window, and 31 of
>    45 compounds pass everywhere. Worth raising specifically: `NaDONA` fails in
>    Chicken (246–267%) but passes in Oyster (77–91%), which points at the matrix
>    rather than the compound; `FpeSA-I` Chicken low reads 434% off a background
>    detected in a single blank; `FpePA` is 0.03% in Oyster high and censored in
>    the other three. These are results to interpret, not necessarily bugs.
> 3. **The spec has not been updated for §6.** Noel was asked and had not
>    answered. Per the rule below, ask again — never edit the spec unprompted.
>    The edits §6 needs: §6.1.3/6.1.4 "the" low and high spike sample → a set
>    grouped by matrix; §6.1.5 asks for sample masses §4 already has, so the code
>    reuses them rather than asking twice; §6.1.6 nominal concentrations in the
>    compound list → the per-matrix `spike_table`; a non-detect background is
>    averaged over detected values only; and the 70–130% window belongs in §6,
>    which currently states it only for EIS in §7.6.
> 4. **The §6 fill-in block is 57 lines** and about half is name-validation that
>    is now the third near-copy (§4 masses, §5 method blanks, §6 spike sets). §7
>    needs a fourth for the NIS list and NIS-to-EIS assignments. Factor it into
>    one small named helper *before* writing §7, not after.
> 5. **The raw data does not travel with this repo.** `*_RawData/` and `runs/`
>    are gitignored because the repository is public, so a fresh clone has the
>    code but no exports and no run folder. To re-run the verification on another
>    device, Noel has to copy `26_08_04_Oyster_RawData/` across by hand, then
>    `python new_run.py <name>` and point `answers.yaml` at it. Ask for the data
>    rather than assuming the pipeline can be executed.
> 6. **The template now carries this batch's values**, by Noel's explicit
>    decision on 2026-09-22, so `new_run.py` copies start pre-filled with the
>    oyster masses. The validation catches sample *names* that aren't in a new
>    batch but will not catch a *mass* that happens to be valid. Flag this when
>    the next batch starts.

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
