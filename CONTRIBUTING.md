# Contributing

This repo uses a branch and pull request flow. `main` stays releasable and
every change lands through a PR so there is a reviewable history, even for
solo work.

## Development setup

```bash
uv sync --extra dev            # install with dev tools
make lint                      # ruff check
make format                    # ruff format
make test                      # pytest
make up                        # start the stack (gateway + dependencies)
make down                      # stop it
```

The full command list is in the [Makefile](Makefile) (`make help`).

## Workflow

1. Branch off `main` with a short, prefixed name:

   ```bash
   git checkout main && git pull
   git checkout -b feat/semantic-cache       # or fix/, chore/, docs/
   ```

2. Make the change. Keep commits focused and write them in plain language.

3. Run the checks locally before pushing:

   ```bash
   uv run ruff check . && uv run ruff format --check . && uv run pytest
   ```

4. Push and open the PR:

   ```bash
   git push -u origin HEAD
   gh pr create --fill
   ```

5. Let CI go green, then merge (squash keeps `main` linear):

   ```bash
   gh pr merge --squash --delete-branch
   ```

## Conventions

- No em dashes in prose, docs, or code comments; plain developer voice.
- Real API keys live only in `.env` (gitignored), never in `.env.example`.
- Update the docs in the same PR as the behavior change they describe.
