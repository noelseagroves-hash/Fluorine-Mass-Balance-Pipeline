# Working on this project

Notes for Claude. `START_HERE.md` covers setting a machine up; the notebook's own
first cell is where the batch workflow is described, and it is the single place
that describes it.

## What this is

`TA_Processing.ipynb` implements `TA Code Spec.md`: raw targeted-analysis exports
from an LC-MS in, a censored and QC-assessed PFAS dataset out.

**The pipeline is complete.** §1 to §11.2 are implemented, verified against the
26_08_04 Oyster batch and signed off. §11.3 figures was cut by Noel on 2026-09-27
rather than built. Work from here is maintenance and the occasional new batch, not
construction, so the build-order rhythm below no longer applies — but the rules
about how it is built still do.

The notebook's first cell is written for a new lab member, not for Noel and not for
progress tracking. `git log` is the source of truth for what changed.

## How Noel wants this built

**One change per increment.** Propose it, get approval, implement it, then show
evidence it works on real data — actual row counts, computed values, named samples
— before proposing the next. This applied to building the sections and applies
equally to changing them.

**Then prompt to update the spec.** Once Noel says a change is good, ask whether to
update `TA Code Spec.md` to match what the code does, naming the specific edits.
Never edit the spec unprompted. This is why the spec describes the pipeline
accurately rather than drifting from it.

**When changing finished code, prove the output did not move.** Capture
`final_data.xlsx` before touching anything, then compare it sheet by sheet
afterwards; the `About` sheet's timestamp is the only cell allowed to differ. A
refactor that changes a number is a bug, and the comparison is how you know.

**Compactness is a hard requirement.** An earlier attempt at this project was
abandoned because the code grew too long for Noel to keep a handle on. Keep
processing cells under about 30 lines; when one would outgrow that, factor the
repeated part into a small named helper rather than letting it sprawl. Keep
verification prints in cells separate from processing logic. Report the line count
per section, and flag a section trending long before it becomes a problem.

**The audience is a lab member with little coding experience.** Every section gets
a plain-language markdown cell above it saying what it does and why, in terms a
chemist reads. Prefer explicit visible pandas operations over clever abstractions.

Do not let a Python rule become something they have to learn around. `solid`,
`liquid` and `auto` are bare words in §4 so quoting never matters, and `EXCLUDE` in
the amendments cell takes written lines separated by `|` rather than a list of
tuples — that one was rewritten after a missing comma raised `TypeError` three
times before any validation could run. When an input cell can be got wrong, the
error must name the line and suggest the nearest valid name.

**All logic lives inline in the notebook**, not in an imported package. This was a
deliberate choice, accepting worse pull-request diffs, so that every step is
readable in place.

## The verification loop that matters

Every bug found so far was found by running real data, not by reading code. Two of
them — a pandas `str` dtype that refuses to hold numbers, and instrument blanks
being compared against limits in a different unit — were invisible to inspection
and only appeared when real arithmetic hit real values.

A third was found by running the pipeline against batches it had not seen:
filtering a dataframe and then assigning a column taken from the parent aligns
correctly only while the filtered frame is non-empty. On a batch with no check
standards the empty frame took the parent's index and invented 3,589 rows. Test a
section against a batch that lacks what it looks for, not only against this one.

So: implement, run, and read the output before claiming anything works.

The batch lives in `runs/<name>/`, gitignored. Execute it headlessly rather than
asking Noel to run it, **using the fluorine environment's jupyter, not the base
one**:

```
cd runs/<name>
/opt/anaconda3/envs/fluorine/bin/jupyter nbconvert --to notebook --execute \
    --allow-errors --output <somewhere-temporary>/run.ipynb TA_Processing.ipynb
```

Base and `fluorine` hold different major versions of pandas. Verifying in base
proved nothing about what Noel's kernel would do, and `openpyxl` was present in one
and missing from the other, which is how §11 came to fail for Noel after I had
reported it working.

`--allow-errors` is important: without it nbconvert writes no output notebook when
a cell raises, so you get the traceback but not the prints that led to it. Then
read each cell's `outputs` from that JSON.

Assertions in the check cells have caught several of my own errors. Keep adding
them; they are not decoration.

## If a lab member asks for help running a batch

This is a different job from the one the rest of this file describes, and the
difference matters. They are operating the pipeline, not changing it.

**Walk them through the notebook's own first cell rather than replacing it.** It is
written for exactly this and is the single place the workflow is described. If it
turns out to be unclear, that is worth fixing in the notebook so the next person
benefits — not worth talking them past.

**Do not supply their scientific inputs.** Sample weights, which samples were
method blanks, which samples are spikes, what to exclude after a QC review: these
are theirs to provide and theirs to defend. Filling them in produces numbers that
look plausible and are wrong, and they are the one who will be asked why. Read
back what they typed and check it against the batch; do not invent it.

**Ask where the export folder is.** It is not in the repository and never will be,
so nothing can be verified until they say where it is on their machine.

**Fix their run copy, not the template.** A batch that stops because an input is
wrong is fixed by correcting the input. Changing the template to accommodate one
batch breaks it for everybody. If the pipeline itself is genuinely at fault, that
is the development path: branch, pull request, review.

**Run All, not single cells.** Almost every "something is not defined" is this.

**Their run folder is theirs.** Never copy the template over it — that destroys
whatever they have typed. I did it twice while building this.

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

## What only the scientist can supply

Some values exist nowhere in the data. Ask rather than infer:

- each sample's weight or volume, and the batch's phase (§4)
- which samples served as method blanks (§5)
- the low and high spike amounts in ng, and which samples are the spikes and their
  backgrounds (§6)
- which samples belong to which matrix (§7)

The spec calls several of these "hard coded". They are not in the exports, and
guessing them would produce numbers that look plausible and are wrong.

Method constants are settled and live in the notebook: the spike factor per
compound (§6), the NIS list and the NIS-to-EIS pairs (§7), and the compound renames
that strip the exports' `-I` suffix (§1). They describe the method rather than a
batch, so a new batch does not restate them — but confirm them with Noel if the
method changes.

**A run folder belongs to whoever is running that batch.** Do not copy the template
over it: that destroyed Noel's typed `EXCLUDE` list once. If the template changes
and a run needs it, say so and let them decide.
