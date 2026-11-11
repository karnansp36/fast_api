# Contributing to TaskPilot

Thanks for your interest in improving TaskPilot! Contributions can include bug fixes, agent/task integrations, API improvements, documentation, tests, and improvements to the chat experience.

## Before you start

1. Search existing issues and pull requests to avoid duplicate work.
2. For substantial changes, open an issue first to discuss the scope and approach.
3. Keep changes focused. Prefer a small PR that does one thing well.
4. Do not copy code from another project unless its license permits reuse. Preserve required notices and credit the original authors. TaskPilot uses the MIT License; that does not change the license terms of third-party code or dependencies.

## Local development

Follow the [README quick start](Readme.md#quick-start) to install dependencies and configure PostgreSQL, pgvector, Redis, and a model provider. Copy `.env.example` to `.env` and use local credentials only.

Run the API locally:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Apply database migrations when your local database is ready:

```bash
alembic upgrade head
```

Start Celery only when developing or validating background task flows:

```bash
celery -A app.celery_worker:celery worker --loglevel=info
```

## Making a change

- **API changes:** update the relevant router and document endpoint behavior and response shapes.
- **Agent changes:** keep agent instructions and tool inputs explicit; validate outputs and handle provider failures.
- **Task automation:** make task execution observable, report failures accurately, and avoid telling users an action succeeded unless it did.
- **Database changes:** add a reviewed Alembic migration; do not rely on manual schema edits.
- **UI changes:** keep the browser interface accessible, responsive, and safe when rendering user/model text.
- **Configuration:** add new settings to `app/config.py` and `.env.example`; provide safe development defaults and never add secrets.
- **Dependencies:** justify new runtime dependencies and update the appropriate requirements file.
- **Tests:** add or update tests for changed behavior. External services should be isolated or mocked where practical.

## Validation

Before submitting a pull request, run checks relevant to your change. At minimum, check Python syntax and inspect the diff:

```bash
python -m compileall app migrations
 git diff --check
```

If you add tests, run them and include the command and result in your PR description. This repository does not yet define a complete automated test or lint suite; avoid claiming tests passed unless you ran them.

## Pull request checklist

- [ ] The PR has a clear title and explains the problem and solution.
- [ ] The change is focused and follows the existing application structure.
- [ ] Relevant tests or manual verification steps are included.
- [ ] API, configuration, migration, and README documentation are updated as needed.
- [ ] No secrets, local databases, logs, generated files, or personal data are included.
- [ ] Breaking changes and deployment considerations are clearly noted.

## Reporting security issues

Do not publish credentials or sensitive personal data in a public issue. If you discover a security concern, report it privately to the repository maintainer through GitHub's available private reporting options.
