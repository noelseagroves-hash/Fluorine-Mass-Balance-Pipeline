# Branching Strategy

This project uses a protected-`main` workflow. Please follow these rules so we keep a clean, working `main` branch at all times.

## Rules

1. **`main` is protected.** No one — including admins — can push directly to `main`. All changes must come in through a pull request.
2. **Each member works on their own branch.** Create a branch off `main` for your work and commit there.
3. **Open a pull request into `main` when ready.** GitHub will run any checks and let others review before merging.
4. **Force-pushes and branch deletion on `main` are blocked**, so history stays intact.

## Workflow

```bash
# 1. Make sure your local main is up to date
git checkout main
git pull

# 2. Create your branch
git checkout -b <your-name>/<short-feature-description>

# 3. Work and commit as usual
git add .
git commit -m "Describe your change"

# 4. Push your branch
git push -u origin <your-name>/<short-feature-description>

# 5. Open a pull request into main on GitHub, then merge once it's ready
```

## Branch naming

Use `<your-name>/<short-description>`, e.g. `noel/fix-fluorine-calc` or `noel/add-import-script`.

## Notes

- Pull requests don't require an approval to merge, but should still be opened so changes are visible and reviewable before landing on `main`.
- Keep branches focused and short-lived — merge (or delete) them once the PR lands.
