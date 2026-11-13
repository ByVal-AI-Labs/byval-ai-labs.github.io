# ADLC Portal

**https://byval-ai-labs.github.io/adlc-portal/**

The ADLC guide and ByVal AI Labs capabilities in one place, for stakeholders.

This repository is **public**, and so is everything in it. Each section is built in its own
(usually private) source repository and pushed here as finished pages only, never as source code.

## How it works

```
private repo A ──push built pages──▶ guide/      ┐
private repo B ──push built pages──▶ metrics/    ├─▶ deploy-portal.yml ─▶ GitHub Pages
private repo C ──push built pages──▶ showcase/   ┘    (landing page built from every meta.json)
```

- Every top-level folder with a `meta.json` and an `index.html` is a **section**. Folders that
  start with `_` or `.` are portal internals.
- On every push to `main`, `.github/workflows/deploy-portal.yml` runs `_portal/build_portal.py`. It
  validates each section, renders the landing page from `_portal/template.html` and deploys the
  site.
- A section that breaks the contract is **skipped with a warning** in the workflow log, and the
  rest of the portal still deploys.

## Current sections

| Folder | Published by | Workflow |
|---|---|---|
| `guide/` | ADLC template repository | `.github/workflows/guide-pages.yml` |
| `governance/` | ADLC template repository | `.github/workflows/guide-pages.yml` |

## Add a section

### 1. The contract

Your source repository owns exactly one folder, for example `metrics/`:

```
metrics/
  index.html     entry page; any other assets (css, js, images) next to it, linked relatively
  meta.json      the landing-page card
```

`meta.json`:

```json
{
  "title": "Delivery metrics",
  "description": "Cycle time, AC coverage and review findings across slices.",
  "owner": "Team name",
  "category": "Showcase",
  "order": 20,
  "updated": "2026-11-13T09:00:00Z"
}
```

| Field | Required | Meaning |
|---|---|---|
| `title` | yes | Card heading |
| `description` | yes | One or two sentences |
| `owner` | no | Team or person shown on the card. Don't name private repositories. |
| `category` | no | Groups cards under a heading (default `General`) |
| `order` | no | Integer; lower comes first, both for categories and for cards within one (default `100`) |
| `updated` | no | ISO 8601 timestamp, normally set by the publishing workflow |

Folder names use lowercase letters, digits and hyphens. A link back to the portal from your page
is `../`.

### 2. Credentials

Each source repository gets its own SSH deploy key:

1. Generate a key pair locally: `ssh-keygen -t ed25519 -N "" -f key`.
2. Add `key.pub` to **this** repository as a deploy key with write access:
   `gh repo deploy-key add key.pub --repo ByVal-AI-Labs/adlc-portal --allow-write --title "<source repo> publish"`.
3. Store the private half `key` as a secret in the **source** repository:
   `gh secret set PORTAL_DEPLOY_KEY --repo <owner>/<source repo> < key`.
4. Delete both local key files.

A deploy key can write to the whole repository. Each source repository should touch only its own
folder, and the publishing workflow below does exactly that. With many source repositories, switch
to a single GitHub App whose credentials are shared as organisation secrets.

### 3. Before you publish

The portal is public. Before a section goes live, confirm that it contains:

- no client names, logos, data, or screenshots of client systems;
- no names of private repositories, internal hostnames or credentials;
- metrics only from internal or reference projects (client aggregates need the client's permission);
- only claims that are true today. Mark aspirations as such.

### 4. Publishing workflow (in the source repository)

Copy `.github/workflows/guide-pages.yml` from the ADLC template and change its `matrix` entries
(`section`, `build`, `page`, `meta`). Run it manually with `dry_run` first. That builds the pages and
checks push access without publishing anything. It replaces your folder in this repository on every run, writes
`updated` into your `meta.json`, and retries the push if another section published at the same
moment.
