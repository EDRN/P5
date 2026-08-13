# 🎛 EDRN Site Testing

This [Django](https://www.djangoproject.com/) app provides browser-based smoke testing for the [Early Detection Research Network](https://edrn.nci.nih.gov/) portal.

## Prerequisites

- Firefox installed on the machine running the tests
- The portal running and reachable at `BASE_URL`
- For local testing: a populated database (`task dev-rebuild` or equivalent) so search and index pages have content
- `edrnsite.test` installed in the project virtual environment (`task venv`)

Selenium 4.9 includes Selenium Manager, which usually downloads `geckodriver` automatically.

## Running smoke tests

Start the site in one terminal:

```console
task run
```

Run the smoke tests in another:

```console
task e2e
```

Against production (read-only checks only):

```console
BASE_URL=https://edrn.nci.nih.gov/ task e2e
```

Watch the browser instead of headless mode:

```console
EDRN_E2E_HEADLESS=0 task e2e
```

Without Taskfile:

```console
.venv/bin/django-admin test edrnsite.test.tests --settings local --pythonpath . --tag=smoke -v2
```

## 🍃 Environment variables

| Variable            | Default                  | Purpose                               |
|:--------------------|:-------------------------|:--------------------------------------|
| `BASE_URL`          | `http://localhost:6468/` | Target portal base URL                |
| `EDRN_E2E_HEADLESS` | `1`                      | Set to `0` to show the Firefox window |


## 🩺 What is covered (Tier 1)

- Home page load, login link, main navigation sections
- Static luggage-tag logo asset
- Search page results (or empty-results message) and header search form
- Protocol index DataTable (global/column search, PI/field/collab filters, sort, pagination, export buttons)
- Member Finder facet form and results container

Form submission, authentication flows, and AI search summary are deferred to future integration tests.


## 🔮 Future: isolated integration tests

`EDRNLiveSiteTestCase` in `base.py` is reserved for Phase 2 tests that spin up Django's `StaticLiveServerTestCase` with an ephemeral test database. Those will use `@tag('integration')` and run separately from smoke tests.
