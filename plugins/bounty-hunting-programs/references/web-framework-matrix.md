# Web and API Framework Matrix

Use this matrix after detecting the server stack.

| Stack | Signals | Priority Surfaces | Preferred Building Blocks |
| --- | --- | --- | --- |
| Express / Fastify / NestJS | `package.json`, `src/controllers`, decorators, middleware chains | auth middleware order, admin flags, SSRF helpers, file upload handlers, background jobs | `audit-context-building`, `sharp-edges`, `insecure-defaults`, `variant-analysis` |
| Next.js / App Router | `app/`, `pages/api`, server actions, edge handlers | server actions, internal fetches, cache poisoning, middleware bypasses, preview/admin flows | `audit-context-building`, `sharp-edges`, `insecure-defaults`, `agentic-actions-auditor` |
| Django / DRF | `settings.py`, `urls.py`, serializers, viewsets | object-level auth, serializer trust, admin exposure, storage backends, Celery tasks | `audit-context-building`, `sharp-edges`, `insecure-defaults`, `supply-chain-risk-auditor` |
| Flask / FastAPI | routers, dependency injection, Pydantic models | dependency injection trust, background tasks, file handling, internal admin routes | `audit-context-building`, `sharp-edges`, `insecure-defaults` |
| Rails | `config/routes.rb`, controllers, jobs, concerns | `before_action` gaps, strong params, ActiveStorage, signed routes, job replay | `audit-context-building`, `sharp-edges`, `variant-analysis` |
| Laravel / PHP | `routes/`, policies, guards, queues | policy gaps, mass assignment, signed URLs, queue workers, deserialization | `audit-context-building`, `sharp-edges`, `insecure-defaults` |
| Spring / Java | controllers, `@PreAuthorize`, `application.yml`, actuator | method security gaps, SpEL, deserialization, actuator/admin surfaces, async jobs | `audit-context-building`, `sharp-edges`, `supply-chain-risk-auditor` |
| Go HTTP Services | `main.go`, routers, handlers, middleware | auth middleware order, path normalization, template handling, SSRF, proto/json parsing | `audit-context-building`, `fuzzer`, `variant-analysis` |
| ASP.NET / C# | controllers, attributes, Razor/Blazor, `appsettings.*` | attribute gaps, model binding trust, file upload/storage, internal admin endpoints | `audit-context-building`, `sharp-edges`, `insecure-defaults` |

## Common Bug Classes

- Broken object-level authorization
- Multi-tenant isolation failures
- SSRF and internal metadata access
- File upload, archive extraction, or path traversal
- Webhook trust and replay failures
- Queued or async job abuse
- Dangerous defaults in auth, CORS, debug, or storage configuration
