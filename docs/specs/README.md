# Feature specifications

Specifications are the source of truth for a feature or cross-cutting change.
They should be short enough to use during implementation and specific enough to
test. Use [_template.md](_template.md); keep approved specifications in this
directory with a descriptive kebab-case filename.

When the change needs approval, record the approver and calendar date directly
below `Status`. Do not replace that record after implementation; it is the
auditable decision trail for the change.

Do not create a spec for a trivial, isolated correction. Record the task and
acceptance criterion instead, then add a regression test.
