# TA Processing Pipeline — Design Decisions

Date: 2026-09-15
Status: Approved for implementation, Step 1
Spec of record: [`TA Code Spec.md`](../../../TA%20Code%20Spec.md)

This document does not replace `TA Code Spec.md`. It records the places where the
implementation deliberately departs from that spec, and why. Anyone reviewing the
notebook should read this first — several departures exist because the spec was
written before it was checked against real instrument exports, and coding the spec
literally would produce a pipeline that silently processes zero rows.

## Where the spec and the real exports disagree

Verified against a real `Quantitation_ByCompound` PFOS export.

| `TA Code Spec.md` says | Real export contains | Spec section that breaks |
|---|---|---|
| `Sample Type = "Blank"` for instrument blanks | `"Matrix Blank"` | §7 Method 1, §9 |
| `Sample Type = "Check Standard"` | `"Chk Std"` | §10 |
| `ISTD Actual RT` | `ISTD Actual Rt` | §7 |
| `Sample Name (Batch Ordering)` as one column | separate `Sample Name` and `Sample Order` | §1 |
| EIS theoretical value `5000 ng/L` | `ISTD Amount = 4795` | §7 Method 2 |

§2.3 also reads "Cat Std" where "Cal Std" is meant.

Each of these is an exact string comparison in the spec. A mismatch does not raise an
error — it matches no rows and yields an empty result, which is the failure mode most
likely to go unnoticed in a QC pipeline.

Further facts about the real data that the spec does not mention:

- Exports carry **30 columns**, not the 14 listed in §1.3.
- `N/F` appears as a literal string inside otherwise-numeric columns when a compound
  was not found.
- `Theoretical Amount` is the string `"N/A"` for every non-standard sample.
- `Calculated Amount` is **negative** in some blanks (e.g. `-0.106`, `-1.586`).
- `Noise` and `Signal to Noise` can contain `"Peak index not specified"`.
- Each export file holds exactly **one compound**; the master list is the
  concatenation of files. NIS compounds must therefore be exported as their own
  files for §7 and §8 to have data to work with.

Consequence: no numeric column may be read with a fixed float dtype. Every one needs
explicit coercion with the original sentinel preserved.

## Design decisions

### 1. Sample Type vocabulary as named constants

The four sample-type strings are defined once as constants, and a validation step
asserts that every `Sample Type` observed in the loaded data is one of them.

Coding the spec's literals directly would mean §9 and §10 quietly match nothing.
Defining them in one place makes the mismatch visible, makes the fix a single-line
edit if the instrument software changes its wording, and turns an unnoticed empty
result into a loud failure at load time.

### 2. Censoring replaces the value in place (follows spec)

§3.3 and §3.4 say to replace the value in `Calculated Amount` with the string
`"<LOQ"` or `">ULOQ"` according to which bound was crossed. The implementation does
exactly this: the censored value is overwritten by the label, in the
`Calculated Amount` column itself.

This is not a departure — it is recorded here because it determines how every later
step must be written. `Calculated Amount` is an `object` column carrying a mix of
numbers and the labels `N/F`, `<LOQ`, and `>ULOQ`. The spec anticipates this
directly: §4.1.4 instructs that when the value is one of those labels, the label is
left as is and the EF is not applied.

Therefore every downstream step that does arithmetic on `Calculated Amount` —
§4 EF application, §5 MDL averaging and censoring, §6 spike recovery — must first
exclude the label values explicitly, and must preserve them unchanged in the output.
Steps are written so that a label can never be silently coerced to `NaN` or dropped:
a censored cell means "a measurement exists but falls outside the quantifiable
range," which is different from missing data and is reported as such.

### 3. Filtering marks rows rather than deleting them

§2.4 says an RT-invalid row "is deleted from master list." The implementation marks
`rt_valid = False` and filters, retaining the excluded rows in an audit table.

The QC report required by §11.2 has to show what was removed and why. Deleting rows
outright destroys the evidence the report is supposed to present.

### 4. Scientist inputs persist to an answers file

§1.1, §4.1.2, §5.1.1, §6.1.2 and §7.1 all prompt the scientist for input. Those
answers are written to `answers.yaml`, and the pipeline reads its inputs from that
file.

The spec's two-pass structure reruns the entire pipeline on a QC-adjusted dataset.
Without persisted answers, the second pass re-asks every question — roughly forty
prompts including a sample mass for each sample. Persisting them also makes a run
reproducible months later and lets the processing steps be checked without
simulating keyboard input.

### 5. All logic inline in the notebook

Processing code lives in notebook cells rather than an imported package, so the
scientist responsible for defending these numbers can read every operation in place.

The accepted cost is that notebook JSON produces poor pull-request diffs. Revisit if
the notebook becomes unreviewable.

### 6. Template in the repository, batch runs outside it

`TA_Processing.ipynb` in the repository root is a template: the code with the
per-batch inputs left blank. A batch is processed in a copy under `runs/`, which
is gitignored.

This keeps the shared code reviewable while batch masses, results and figures stay
local, and it makes each run a frozen record — a later fix to the template cannot
reach back and silently change a result that has already been reported. The cost
is that a fix does not reach old runs either; re-running a batch against the
current template is a deliberate act, which is the correct default for results
that have been published or handed to a TA.

A run copy belongs to whoever is running that batch, who is free to edit it
however they like — nothing in a run reaches anyone else. Only changes intended
for everyone go through the template, on a branch and as a pull request. Review
is reserved for the shared code rather than imposed on someone's own working
analysis.

### 7. Real data stays out of the repository

The repository is public and the exports are unpublished measurements. Real data is
referenced by a path in `answers.yaml` and both are gitignored. A small synthetic
fixture reproducing the structure and quirks above is committed so the checks run
for anyone who clones the repository.

## Build order

One spec step per increment, each verified against real exports before the next
begins.

| Increment | Spec sections | Output to verify against |
|---|---|---|
| 1 | §1 Readfile | Observed sample types, per-file row counts, compound list, `N/F` rows, retained column dtypes |
| 2 | §2 RT Validation | Per-compound mean Cal Std RT, count and identity of rows failing the ±0.4 min window |
| 3 | §3 LOQ/ULOQ | Per-compound LOQ and ULOQ, counts censored at each bound |
| 4 | §4 Extraction factor | Per-sample EF, the ng/L to ng/g conversion, results in the batch's units |
| 5 | §5 MDL/MRL | Per-compound MDL or MRL, how many method blanks each rests on, counts censored at the limit |
| 6 | §6 Spike recovery | Nominal concentration per matrix and level, background means and the samples each rests on, recoveries against the 70–130% window |

§1–§6 are implemented and verified against the 26_08_04 Oyster batch. §7–§11 remain
out of scope until the section before them is confirmed correct on real data, since
each consumes the output of the ones before and an error propagates.

## Open questions

These need a decision before the section that depends on them is implemented.

1. ~~**`Sample Name (Batch Ordering)` mapping** (blocks §1).~~ **Resolved
   2026-09-23.** Read as the `Sample Name` column, since §1.3 lists `Sample ID`
   separately and `Sample Name` holds the batch-order numbering. Confirmed by §1–§6
   running correctly against the real exports, where samples are addressed
   throughout by `Sample Raw File Name` with `Sample ID` carried alongside as the
   human-readable label.
2. ~~**N/F rows during RT validation** (blocks §2).~~ **Resolved 2026-09-23.** An
   `N/F` row has no RT to validate, because `Method Apex RT` is itself `N/F`. The
   row is retained with `N/F` left in place in `Calculated Amount` rather than
   dropped, because "looked for and not found" is information §9's blank assessment
   wants. §6 treats such a background as a non-detect, contributing no value to the
   background mean.
3. **EIS theoretical value** (blocks §7). The spec says `5000 ng/L`; the data carries
   `ISTD Amount = 4795`. Unresolved whether the constant or the column is correct.
4. ~~**Multiple spike pairs** (blocks §6).~~ **Resolved 2026-09-22.** §6 takes a
   `SPIKE_SETS` mapping of matrix name to its low spike, high spike and background
   samples, so any number of matrices works. This batch has two, Oyster and Chicken.
5. **Values the spec calls hard-coded** (blocks §6 and §7). These exist nowhere in
   the exports and can only come from the scientist. Noel supplies each one when its
   section is reached, rather than any of it being guessed:
   - ~~spike factor per compound (§6.1.1)~~ **supplied 2026-09-22**, now the
     `SPIKE_FACTORS` table in §6
   - the NIS compound list (§7.2)
   - the NIS-to-EIS assignments used by Method 2 (§7.3), including which EIS
     compounds have no corresponding NIS


## §6 spike recovery — departures and decisions (2026-09-22)

- **Results live in their own table.** §6.1.6 and §6.1.9 put nominal concentrations
  and recoveries as columns on the compound list, which assumes a single spike pair.
  With a pair per matrix that would need four columns per quantity, so §6 builds
  `spike_table`, one row per compound per matrix per level.
- **Sample masses are not asked for twice.** §6.1.5 asks the scientist to input the
  mass of each spike sample, but §4 already holds every Unknown sample's amount.
  §6 reads `sample_table['amount']`, so the two cannot disagree.
- **Six compounds are named differently by the instrument than by the method.** The
  method writes `10:2 FTCA`, `8:2 FTCA`, `6:2 FTCA`, `7:3 FTCA`, `5:3 FTCA` and
  `3:3 FTCA`; the exports call the same compounds `FDEA`, `FOEA`, `FHEA`, `FhpPA`,
  `FpePA` and `FprPA`. `SPIKE_FACTORS` is keyed to the export names with the method
  name in a comment. All six carry a factor of 1, so nothing numeric turns on it.
  A mismatch between the factor table and the batch's compounds raises rather than
  silently dropping compounds out of the recovery table.
- **A censored background averages over what was detected.** Noel's decision,
  2026-09-22. §5 censors most background results, so the background mean is taken
  over uncensored values only, and a compound detected in no background sample is
  treated as having no measurable background. `backgrounds_detected` records how
  many samples each mean rests on. The alternatives considered and rejected were
  counting a non-detect as zero, and substituting half the limit.
- **Oyster background is the M oysters only** (`TA_04`–`TA_06`), not all nine, since
  the spikes were made from M oyster material. Noel's decision, 2026-09-22.
- **The 70–130% window is applied in §6.** The spec states it only for EIS recovery
  in §7.6, but Noel confirmed on 2026-09-22 that it governs spike recovery too.
  `RECOVERY_MIN_PCT` and `RECOVERY_MAX_PCT` sit with the method constants so §7 can
  use the same pair.
- **A spiked result that is itself censored is flagged, not skipped.** It gets
  `no recovery, spiked result censored` rather than an empty cell, because an
  unmeasurable spike is a QC finding.

**Signed off by Noel, 2026-09-23.** The arithmetic was verified against the raw
exports and re-run independently on a second device, and the chemistry has now been
reviewed. `FhxSA`'s Oyster background mean was traced by hand from the raw CSV
through the per-sample EF to 0.293795 ng/g and agrees with the pipeline. Note the
order of operations that trace established: each background sample is converted to
ng/g using its own mass *before* the mean is taken, which is not the same number as
averaging the raw ng/L values and applying one EF built from the mean mass.
