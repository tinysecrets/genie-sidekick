# Release Checklist

## Backend and frontend checks

Use lockfile-based dependencies where present. For the frontend, run:

```bash
cd frontend
npm run build
```

The current frontend package defines dev/build/preview scripts but no test or lint script. Do not claim those gates passed when no command is defined. For backend changes, run the repository's available tests or add a disposable-local integration test for the changed route; never point tests to the configured cloud deployment.

## Security and deployment

1. Verify missing/invalid sessions are rejected and the configured admin can log in using test-only credentials.
2. Verify JWT signing secrets and provider keys are supplied through environment configuration and never embedded in the frontend build.
3. Exercise the app against a disposable MongoDB database and local/mock LLM provider, keeping outbound email/other integrations disabled.
4. Review CORS, host binding, cookie flags, dependency changes, `git diff --check`, and the staged diff.
5. Confirm the deployed revision and private network exposure; preserve a known-good commit for rollback.
