# Setting up to process a batch

This covers getting your machine ready. **Everything about actually running a
batch is in the notebook itself** — open it and the first cell walks you through
it, start to finish. This file exists so there is one place describing the
workflow rather than two that drift apart.

You do not need to know Python.

## Once per computer

1. Install [Miniconda](https://www.anaconda.com/download/success) — on Windows
   pick the 64-bit installer and accept the defaults.

2. Open the **Anaconda Prompt** from the Start menu (or Terminal on a Mac), go to
   this folder, and run:

   ```
   conda env create -f environment.yml
   conda activate fluorine
   python -m ipykernel install --user --name fluorine --display-name "Python (fluorine)"
   ```

   The last line makes the environment selectable as a kernel in VS Code.

3. Install [VS Code](https://code.visualstudio.com/), then from its Extensions
   panel install **Python** and **Jupyter**, both by Microsoft.

4. Copy the batch's raw export folder onto the machine. It is not in this
   repository — the exports are unpublished measurements and stay out of version
   control, so somebody has to hand it to you.

## Every batch

Start a run, naming it for the batch:

```
python new_run.py 2026-08-04-oyster
```

That makes `runs/2026-08-04-oyster/` with a copy of the notebook in it. Open
`runs/2026-08-04-oyster/TA_Processing.ipynb` in VS Code, choose
**Python (fluorine)** as the kernel, and read the first cell. It tells you the
rest.

**Use Run All, not one cell at a time.** Each section is built from the ones above
it, so a cell run on its own fails with a message about something not being
defined. That is the commonest way to get stuck, and it is not a real error.

**Never type your batch's numbers into the notebook in the main folder.** That one
is the shared template. `new_run.py` refuses to overwrite an existing run, so it
cannot clobber someone else's work.

## Your run folder is yours

Edit the notebook in it, add cells, print things, try things. Nothing you do there
reaches anyone else, and old runs keep the code they were actually run with — so a
fix made next month cannot quietly change a result you already reported.

If you find a problem with the pipeline itself rather than with your batch, bring
it back to the template so every future batch gets the fix. `CONTRIBUTING.md` says
how: branch, pull request, review.
