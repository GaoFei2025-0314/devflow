# Shipping and Launch Templates

Worked preparation examples for [Shipping and Launch](../SKILL.md). Replace placeholders with project-verified values. These templates do not authorize deployment, rollback, data changes, notifications, cleanup, or a new telemetry integration.

## Feature Flag Check

Use this pattern only when the project already has an applicable flag system and both states are in the verification scope.

```typescript
const flags = await getFeatureFlags(userId);

if (flags.taskSharing) {
  return <TaskSharingPanel task={task} />;
}

return null;
```

Record the flag owner, cohort rule, relevant state tests, removal condition, and what happens when the flag service is unavailable. A flag does not make incomplete work ready to merge.

## Conditional Error Reporting

This example assumes the project already has an authorized error-reporting integration and approved data handling. Minimize identifiers and sensitive request data. Introducing a provider, changing privacy behavior, or sending additional fields is a separate decision.

```tsx
class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean }
> {
  state: Readonly<{ hasError: boolean }> = { hasError: false };

  static getDerivedStateFromError(): { hasError: boolean } {
    return { hasError: true };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    reportError(error, {
      componentStack: info.componentStack,
      routeTemplate: getCurrentRouteTemplate(),
    });
  }

  render() {
    if (this.state.hasError) {
      return <ErrorFallback onRetry={() => this.setState({ hasError: false })} />;
    }
    return this.props.children;
  }
}

app.use((err: Error, req: Request, res: Response, next: NextFunction) => {
  reportError(err, {
    method: req.method,
    routeTemplate: req.route?.path,
  });

  res.status(500).json({
    error: { code: 'INTERNAL_ERROR', message: 'Something went wrong' },
  });
});
```

## Recovery Preparation Template

```markdown
## Recovery Plan for [artifact or release]

### Scope and current state
- Artifact/revision: [immutable identifier]
- Target/environment: [exact target]
- Affected consumers and data: [bounded scope]
- Current rollout state: [deployed/exposure percentage/migration stage]

### Decision criteria
- Hold when: [project-specific criterion and evidence source]
- Recover when: [project-specific criterion and decision owner]
- Observation window: [duration justified by traffic and risk]

### Candidate actions
For each action record its order, prerequisites, expected effect, authority, and verification.

1. Exposure control: [project-verified procedure, if applicable]
2. Artifact recovery: [redeploy/revert/forward-fix procedure selected by project policy]
3. Compatibility restoration: [adapter or routing procedure, if applicable]
4. Data recovery: [verified recovery or reconciliation procedure, if one exists]
5. Communication: [audience and channel, only when separately authorized]
6. Cleanup: [exact objects, only when separately authorized]

### Authorization check
- Action: [concrete operation]
- Target and environment: [exact object]
- Scope: [bounded effects]
- Source: [received instruction or applicable policy]
- Conditions and limits: [checks, window, risk, cost]
- Current validity: [why the record still matches]

### Data and reversibility
- Backup/recovery point: [identity and verified restore scope]
- Non-reversible or lossy effects: [details]
- Customizations and unrelated data preserved: [how]
- Point where forward repair is safer than rollback: [criterion]

### Post-action verification
- Confirm artifact and target: [operation]
- Health and critical flows: [operations]
- Error/latency signals: [project dashboards]
- Data integrity/reconciliation: [operations]
- Result record: [time, environment, source, limits]
```

Thresholds, durations, and commands remain placeholders until selected from project evidence. Do not invent a generic database rollback command: some changes require a forward migration, restore, reconciliation, or an explicit decision about data loss.
