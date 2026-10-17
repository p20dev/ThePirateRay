# Data handling policy

## Authoritative repositories

| Classification | Repository | Examples |
| --- | --- | --- |
| `public` | `ThePirateRay` | Code, tests, plans, schemas, sanitized analysis |
| `private-sensitive` | `ThePirateRay-PrivateStash` | Serial numbers, local usernames, license-related data, private source locators |
| `private-third-party` | `ThePirateRay-PrivateStash` | Vendor binaries, manuals, raw LightBurn/EZCAD files with unclear redistribution rights |

Google Drive is a read-only acquisition source, not a project workspace. No
project artifact is created, edited, renamed, or reorganized there.

## Rules

- Preserve raw bytes. Analysis always produces a new file.
- Record SHA-256, byte size, media type, acquisition time, origin label, and
  classification for every acquired file.
- Keep exact Drive IDs, URLs, machine serials, usernames, and local paths only
  in the private manifest.
- Refer to private evidence publicly using `artifact_id` and `sha256` only.
- Never commit LightBurn Support Data to the public repository.
- Do not execute software acquired from the installer stick during analysis.
- Run the public repository guard before each public push.

## Redaction flow

1. Acquire the original into the private repository.
2. Generate and verify the private manifest.
3. Analyze the original without modifying it.
4. Create a sanitized derivative in the public repository.
5. Run automated guards and manually review the staged diff.
6. Commit and push the private evidence before the public claim that cites it.

During Drive acquisition, authenticated download references are ephemeral and
must be passed to the bounded materializer over standard input. They must not be
written to scripts, manifests, command history, or Git.
