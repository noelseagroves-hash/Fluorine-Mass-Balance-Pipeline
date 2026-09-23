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
| 7 | §7 EIS recovery | Reference areas per EIS, Method 1 recovery per sample and matrix, Method 2 concentration in ng/L against its theoretical, both against the 50–150% window |

§1–§7 are implemented and verified against the 26_08_04 Oyster batch. §8–§11 remain
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
3. ~~**EIS theoretical value** (blocks §7).~~ **Resolved 2026-09-23.** §7 reads the
   theoretical value per compound from the `ISTD Amount` column, not the spec's hard
   coded `5000 ng/L`. Noel confirmed these are properties of the standard used.

   The question was originally framed as `5000` against `4795`, but `4795` was only
   M8PFOS's value, seen because the PFOS export was the one inspected. Across all 78
   exports the column takes eight distinct values over 25 EIS compounds: 18 carry
   5000, while M3PFBS is 4660, M2-4:2FTS 4690, M3PFHxS 4740, M2-6:2FTS 4755, M8PFOS
   4795, M2-8:2FTS 4800 and M2-10:2FTS 4830. The seven that differ are the sulfonates
   and fluorotelomer sulfonates. The value is constant per EIS compound across every
   sample and file, so it is a property of the labelled standard rather than of the
   run. Hard coding 5000 would understate those seven recoveries by up to 6.8%, which
   is enough to move a compound across the 70-130% window.
4. ~~**Multiple spike pairs** (blocks §6).~~ **Resolved 2026-09-22.** §6 takes a
   `SPIKE_SETS` mapping of matrix name to its low spike, high spike and background
   samples, so any number of matrices works. This batch has two, Oyster and Chicken.
5. **Values the spec calls hard-coded** (blocks §6 and §7). These exist nowhere in
   the exports and can only come from the scientist. Noel supplies each one when its
   section is reached, rather than any of it being guessed:
   - ~~spike factor per compound (§6.1.1)~~ **supplied 2026-09-22**, now the
     `SPIKE_FACTORS` table in §6
   - ~~the NIS compound list (§7.2)~~ **supplied 2026-09-23**: M3PFBA, MPFHxA,
     MPFOA, MPFNA, MPFDA, MPFHxS, MPFOS
   - ~~the NIS-to-EIS assignments used by Method 2 (§7.3)~~ **supplied
     2026-09-23**, seven matched pairs; an EIS without a matching NIS gets no
     Method 2 value rather than being assigned one


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


## §7 EIS recovery — departures and decisions (2026-09-23)

Signed off by Noel, 2026-09-23.

- **The EIS peak area is read from the labelled standard's own row.** §7.4 says
  to take it from the `ISTD Area` column on the target rows. §2 drops a target
  row whose retention time failed, and the EIS area on that row goes with it —
  163 of 425 sample/EIS pairs lost, including 13 of the equipment blank's 25.
  Each labelled standard is exported as its own file, and that row survives
  independently: 2 of 425 lost. Where both sources exist they agree to within
  0.5 counts, and a check asserts it so a real divergence is still caught.
- **EIS is derived, not listed.** §1 already splits labelled standards from
  targets by whether a compound has an internal standard of its own. EIS is
  those labelled standards minus the hard coded NIS list, asserted equal to the
  compounds the exports use as an ISTD. Noel's rule: a compound is EIS or NIS,
  never both. Several names differ by two characters (`M3PFBA`/`MPFBA`,
  `MPFHxS`/`M3PFHxS`, `MPFOS`/`M8PFOS`), so a misspelling raises.
- **Method 2 runs only on matched pairs.** §7.3 says to prompt for a NIS
  whenever an EIS lacks one. Noel's decision, 2026-09-23: the correction is
  valid only where the NIS matches properly, so the other 18 EIS compounds keep
  their Method 1 value, get no Method 2 value, and are not flagged for it.
- **Method 2 compares ng/L in the vial, with no sample weight.** Noel's
  decision, 2026-09-23. §7.5 as written divides by sample weight, which would
  make recovery a function of the weighing: on this batch it moved M8PFOS Oyster
  between 91.8% and 169.3% across samples of one matrix purely by weight. The
  same amount of EIS goes into every sample whatever it weighed, which is why
  `ISTD Amount` is one value per compound. The theoretical cancels between the
  two steps, but both steps are kept in the code because the ng/L concentration
  is what the scientist checks the chemistry against.
- **`Detected Mass` is an m/z, not an amount.** It holds 498.93 for PFOS across
  a calibration curve running 10 to 50000 ng/L. §7.5 uses it as the mass of NIS
  and EIS in the response factor; carried through the algebra those terms and
  the NIS amount cancel, so none is needed.
- **The EIS window is 50–150%, separate from §6's 70–130%.** Noel's decision,
  2026-09-23; §7.6 stated 70–130, which is the spike window. An EIS is carried
  through the whole extraction and absorbs more variation than a spike measured
  against a known amount of matrix. Both are printed on every run.
- **Matrices are named by the scientist**, as a mapping of matrix to samples
  plus a separate list for samples belonging to none, so a future batch of soils
  from several locations needs only different names. Every Unknown sample must
  appear exactly once.
- **The reference pools cal standards with instrument blanks**, as §7.4 says.
  Confirmed by Noel 2026-09-23 after it was queried: the instrument blanks
  outnumber the cal standards 29 to 12 and read higher, so pooling lowers
  recoveries rather than raising them.

### Open observation — fluorotelomer sulfonate reference stability

Not a defect, and not resolved. The spread of the 41 reference areas rises with
chain length: M2-4:2FTS 9.7% CV, M2-6:2FTS 12.8%, M2-8:2FTS 18.9%, M2-10:2FTS
33.6%, against 7.3% for M8PFOS. M2-10:2FTS's reference samples span a 3.4-fold
range, so the 100% mark its recoveries are measured against is itself unstable.
These four also read high in Oyster (137–183% on Method 1) and none of them has
a matching NIS, so Method 2 offers no cross-check for exactly the compounds
whose reference is weakest.

Noel could not say on 2026-09-23 whether the trend is expected for these
standards. Worth checking against the next batch to tell a property of the
standards from something specific to this run.
