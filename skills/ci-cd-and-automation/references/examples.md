# CI/CD Configuration Examples

Worked mechanisms for [CI/CD and Automation](../SKILL.md). These examples use GitHub Actions because that is their concrete provider; they do not require that provider, create an integration, or grant an external action. Keep only jobs required by the project's actual policy and risks.

The Node examples below deliberately show an **npm-locked example project** whose manifest, lockfile, and scripts select these commands. For pnpm, Yarn, Bun, another ecosystem, or different script names, use the project's established commands without mixing managers. Version and provider settings are project-provided values, not freshness recommendations.

## Basic Pipeline for an npm-Locked Project

This hypothetical project requires lint, type-check, test, and build on pull requests. Another project may require a different set.

```yaml
name: CI

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: '<project-node-version>'
          cache: npm

      - name: Install locked dependencies
        run: npm ci

      - name: Lint
        run: npm run lint

      - name: Type check
        run: npm run typecheck

      - name: Test
        run: npm test

      - name: Build
        run: npm run build
```

Do not add a script or audit command merely because it appears in another project's template. A required failing job blocks its dependent delivery gate; preserve its logs and investigate before a reasoned retry.

## Database Integration Job

Use a service job only when integration coverage is required and the test data operation is bounded. This example assumes the npm-locked project has the named scripts and an approved CI secret store.

```yaml
integration:
  runs-on: ubuntu-latest
  services:
    postgres:
      image: '<project-postgres-image>'
      env:
        POSTGRES_DB: testdb
        POSTGRES_USER: ci_user
        POSTGRES_PASSWORD: ${{ secrets.CI_DB_PASSWORD }}
      ports:
        - 5432:5432
      options: >-
        --health-cmd pg_isready
        --health-interval 10s
        --health-timeout 5s
        --health-retries 5

  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-node@v4
      with:
        node-version: '<project-node-version>'
        cache: npm
    - run: npm ci
    - name: Prepare isolated test database
      run: npm run db:test:prepare
      env:
        DATABASE_URL: ${{ secrets.CI_DATABASE_URL }}
    - name: Run integration checks
      run: npm run test:integration
      env:
        DATABASE_URL: ${{ secrets.CI_DATABASE_URL }}
```

Use least-privilege test credentials. Verify teardown and recovery scope separately; never aim this example at a shared or production database.

## E2E Job With Failure Artifact

This example applies only when E2E is required, the install command exists, and artifact upload is allowed. Set project-specific retention and ensure reports contain no secrets or sensitive data.

```yaml
e2e:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-node@v4
      with:
        node-version: '<project-node-version>'
        cache: npm
    - run: npm ci
    - name: Install project-declared browser runtime
      run: npm run e2e:install
    - name: Build
      run: npm run build
    - name: Run E2E checks
      run: npm run test:e2e
    - uses: actions/upload-artifact@v4
      if: failure()
      with:
        name: e2e-failure-report
        path: '<project-report-path>'
        retention-days: '<project-retention-days>'
```

## Manually Authorized Preview Mechanism

A preview is an external deployment. This manual trigger illustrates a mechanism after provider use, target, secrets, cost, and data handling are approved. It does not make an incomplete work package ready for PR.

```yaml
name: Deploy Preview
on:
  workflow_dispatch:
    inputs:
      revision:
        description: 'Reviewed revision to preview'
        required: true
      target:
        description: 'Approved preview target'
        required: true

jobs:
  preview:
    runs-on: ubuntu-latest
    environment: ${{ inputs.target }}
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ inputs.revision }}
      - name: Deploy with the project-approved provider command
        run: '<project-preview-command>'
```

The workflow trigger does not prove that a particular invocation is authorized. Before running it, bind the exact revision, target, scope, source, and conditions of the effective grant.

## Manually Authorized Recovery Mechanism

Recovery may need several steps and may not be a rollback. This mechanism delegates the real operation to a reviewed project script rather than embedding an invented provider command.

```yaml
name: Recover Deployment
on:
  workflow_dispatch:
    inputs:
      target:
        description: 'Exact approved environment'
        required: true
      artifact:
        description: 'Known recovery artifact'
        required: true

jobs:
  recover:
    runs-on: ubuntu-latest
    environment: ${{ inputs.target }}
    steps:
      - uses: actions/checkout@v4
      - name: Run reviewed recovery procedure
        run: '<project-recovery-command>'
      - name: Verify recovered target
        run: '<project-recovery-verification-command>'
```

The commands must be replaced with existing reviewed project entrypoints that consume the bound target and artifact safely. Workflow availability does not authorize an invocation, data deletion, history rewrite, notification, or cleanup.

## Optional Scheduled Dependency Updates

Enable a dependency-update service only when that provider, schedule, ownership, expected PR volume, and secret/data access are approved. The following is an illustrative setting for a repository that already uses Dependabot; it does not create an ongoing automation by appearing here.

```yaml
version: 2
updates:
  - package-ecosystem: npm
    directory: /
    schedule:
      interval: weekly
    open-pull-requests-limit: 5
```

Translate `package-ecosystem` and schedule to the actual project. Generated PRs still require normal dependency-risk review and project gates.

## Parallel Jobs for the Same npm-Locked Example

Parallelize independent mandatory jobs only when their results do not rely on an ordering hidden by the original pipeline.

```yaml
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '<project-node-version>', cache: npm }
      - run: npm ci
      - run: npm run lint

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '<project-node-version>', cache: npm }
      - run: npm ci
      - run: npm test
```

Caching, path filters, sharding, and larger runners are optimizations to justify with measured duration, cost, and coverage. Do not skip mandatory checks or discard failure diagnostics to meet an arbitrary runtime threshold.
