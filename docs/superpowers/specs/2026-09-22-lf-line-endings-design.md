# LF line endings — locked design (2026-09-22)

Windows `core.autocrlf=true` with no `.gitattributes` reports some already-LF files as modified even when `git diff` is empty. Git warns it will replace LF with CRLF the next time it touches them.

## Symptom

`docs/superpowers/specs/2026-09-19-chips-only-find-design.md` and `tests/test_session.py` show as modified. `git ls-files --eol` reports `i/lf w/lf` for both. There is no content change.

## Fix

`.gitattributes` contains exactly:

```
* text=auto eol=lf
```

`eol=lf` overrides `core.autocrlf` for text. `text=auto` leaves PNG, JPG, and WebP as binary. Restore the two phantom paths so their stat matches HEAD. Do not `git add --renormalize` unless `git diff` after the attribute is non-empty.

## Out of scope

Do not change `git config`. Do not track local API capture files (`compose*.json`, `retrieve*.json`, `crous.json`, `health.json`, `*.hdr`).
