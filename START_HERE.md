# Processing a batch

This walks through running the targeted-analysis pipeline on one batch of data.
You do not need to know Python. You will type numbers into a notebook and press
Run.

## Once per computer: set up

1. Install [Miniconda](https://www.anaconda.com/download/success) (pick the
   Windows 64-bit installer, accept the defaults).
2. Open the **Anaconda Prompt** from the Start menu and run:

   ```
   conda install -y -c conda-forge --override-channels pandas pyyaml jupyter
   ```

3. Install [VS Code](https://code.visualstudio.com/), then from its Extensions
   panel install **Python** and **Jupyter** (both by Microsoft).

## Every batch: start a run

The notebook in the main folder, `TA_Processing.ipynb`, is the **template**. It
holds the code with the batch values left blank. Never type your numbers into
it — each batch gets its own copy.

**Either** open the Anaconda Prompt in this folder and run:

```
python new_run.py 2026-08-04-oyster
```

**or** do the same thing by hand in File Explorer: make a folder called `runs`,
make a folder inside it named for your batch, and copy `TA_Processing.ipynb`
into it.

Name the run after the batch — the date and the matrix works well, for example
`2026-08-04-oyster`.

## Fill it in and run it

1. Open your new copy, `runs/<your batch>/TA_Processing.ipynb`, in VS Code.
2. Top right, click **Select Kernel** and choose **Python (miniconda)**.
3. Click **Run All**. The first cell prints `Run folder: <your batch>` — if it
   says `This is the TEMPLATE` instead, you opened the wrong copy.
4. It stops and asks for the folder holding your `..._Quantitation_ByCompound_...csv`
   exports. Paste the path. It is remembered for this run.
5. It stops again at **section 4** and prints a block listing every sample in
   your batch. Copy that block into `SAMPLE_AMOUNTS` in the same cell, fill in
   each mass, and set `PHASE`:

   - `PHASE = 'solid'` — amounts in **grams**, results in **ng/g**
   - `PHASE = 'liquid'` — amounts in **litres**, results in **ng/L**

   Leave the equipment blank as `'auto'`. It has nothing to weigh, so it takes
   the smallest mass in the batch, which gives the most conservative result.

6. **Run All** again.

## Reading what it tells you

Each section prints what it did and checks its own work. A section that finds a
problem **stops the notebook** rather than carrying on with a bad number, and
says which sample or compound is at fault.

Things it will tell you about, all of which are worth reading rather than
scrolling past:

- rows dropped because a compound did not elute where its standards did
- compounds whose LOQ rose because the lowest calibration levels were not
  detected — their results are censored more aggressively than usual
- standards that did not read back at their own concentration

## If something goes wrong

**It asks for the data folder every time.** You are running the template, not a
run copy. Check the first cell's output.

**Values you typed seem to be ignored.** If you edited `answers.yaml` in
Notepad, re-save it in VS Code instead. Notepad adds a hidden marker to the
start of the file that can stop the first line being read.

**A cell shows a red error.** Read the last line — it names the sample or
compound and what is wrong with it. Most stops are missing or impossible input
values, not broken code.

**The numbers look wrong.** Dig into it in your run copy — that is what it is
for. If what you find turns out to be a problem with the pipeline rather than
something particular to your batch, bring it back to the template so every
future batch gets the fix too.

## Changing the code

**Your run copy is yours.** Edit it, add cells, print intermediate tables, try
things. Nothing you do in it affects anyone else, and you do not need anyone's
permission.

**Changes meant for everyone go in the template**, following `CONTRIBUTING.md`:
branch, pull request, review. That is the only part that needs coordinating.

The two are kept separate on purpose. Old runs keep the code they were actually
run with, so a fix made next month cannot quietly change a result you already
reported — and equally, whatever you do in your own run cannot reach anyone
else's.
