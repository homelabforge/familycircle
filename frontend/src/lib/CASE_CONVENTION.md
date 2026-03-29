# Case Convention Decision

## Status: Intentional — No Change Needed

## Current Conventions

- **API response data**: `snake_case` (e.g., `event_date`, `family_id`, `is_super_admin`)
- **React component props, local state, functions**: `camelCase` (standard React/TypeScript)
- **Generated types** (`api.generated.ts`): `snake_case`, matching the OpenAPI spec from the backend

## Why This Is Not a Problem

The frontend uses snake_case for all API data fields because that is what the API returns
and what `openapi-typescript` generates. This is consistent within its domain: every
component, hook, and page that touches API data uses the same snake_case field names.

Meanwhile, React-specific code (component props, event handlers, local state variables,
utility functions) follows standard camelCase conventions. These two domains do not
conflict — they coexist cleanly.

## Why a Response Transformer Was Rejected

Adding a snake_case-to-camelCase transformer in the API client was evaluated and rejected:

1. **Blast radius**: 40+ components, 19 API modules, all hooks, and all pages reference
   snake_case field names directly. A transformer would break every single one simultaneously.
2. **Type safety loss**: The generated TypeScript types from `openapi-typescript` use
   snake_case keys. A runtime transformer would make the types wrong — every field access
   would need manual `as` casts or a parallel set of camelCase type definitions.
3. **Zero practical benefit**: The codebase is already internally consistent. Developers
   know that API data uses snake_case. Converting gains nothing but churn.
4. **Incremental conversion is worse**: Converting file-by-file would create a period where
   some components expect camelCase and others expect snake_case for the same data, making
   the codebase genuinely inconsistent rather than just stylistically mixed.

## Summary

Two consistent conventions in their respective domains is better than one convention
applied inconsistently across a painful migration.
