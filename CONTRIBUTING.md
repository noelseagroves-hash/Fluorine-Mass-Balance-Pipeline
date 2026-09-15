# Branching Strategy

This project uses a protected-`main` workflow. Please follow these rules so we keep a clean, working `main` branch at all times.

## Rules

1. **`main` is protected.** All changes must come in through a pull request — no direct pushes to `main`.
2. **Each member works on their own branch.** Create a branch off `main` for your work and commit there.
3. **Open a pull request into `main` when ready.** GitHub will run any checks and let others review before merging.
4. **At least one peer review approval is required before merging.** Have a teammate review your changes and approve the PR — GitHub will block the merge button until that happens. The repository owner is the sole exception; see [Owner exception](#owner-exception).
5. **Force-pushes and branch deletion on `main` are blocked**, so history stays intact.

## Owner exception

GitHub does not let anyone approve their own pull request — the Approve option is
disabled for a PR's author regardless of what permissions they hold. Because the
repository owner does not always have a reviewer available, admin enforcement is
turned off on `main`, so the owner can merge their own pull requests without an
approving review (the "Merge without waiting for requirements to be met" option).

This exception applies to the repository owner only. **Every other contributor must
open a pull request and get at least one approving peer review before merging into
`main`** — that requirement is unchanged and still enforced by GitHub.

The owner is still expected to open a pull request for every change rather than
pushing straight to `main`, so that each change stays visible and reviewable after
the fact.

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

# 5. Open a pull request into main on GitHub, get it approved by a peer, then merge
```

## Branch naming

Use `<your-name>/<short-description>`, e.g. `noel/fix-fluorine-calc` or `noel/add-import-script`.

## Notes

- Pull requests require at least one approving review before they can be merged into `main` (except for the repository owner — see [Owner exception](#owner-exception)).
- Keep branches focused and short-lived — merge (or delete) them once the PR lands.
