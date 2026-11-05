# Security and data handling

EduAI Suite is an evolving portfolio project. It has not undergone an independent security audit and must not be treated as a production-grade document vault or student-record system.

## Important handling rules

- Use synthetic data for demos and development. Do not upload real identity cards, transcripts, marksheets, certificates, or other sensitive personal records to a public deployment.
- Keep `.env` files, database dumps, generated documents, uploaded originals, and encrypted vault files out of Git.
- Share URLs contain bearer tokens. Anyone who obtains a valid, unexpired token can download the associated document. Send them only to intended recipients.
- Vault uploads are capped at 10 MB. The backend checks the filename extension and upload size; this is not a substitute for malware scanning or content inspection.
- Existing generated documents and encrypted blobs already committed to the repository are not removed by `.gitignore`. Review their content and provenance. If sensitive material was committed, removing it from the latest tree is not enough; Git history may also need rewriting and credentials may need rotation.

## Vault encryption compatibility

The current vault derives a Fernet key from `SECRET_KEY` using PBKDF2-HMAC-SHA256 and a fixed application salt. This implementation is retained for compatibility with files that may already have been encrypted by the project.

**Do not change `SECRET_KEY` casually.** Existing encrypted files may become undecryptable when the derived key changes. A future cryptographic redesign should use a versioned envelope containing a per-file random salt and key-version metadata, plus a deliberate migration path for existing files.

Fernet uses authenticated symmetric encryption; it should not be described as AES-256. Share links are token-based application endpoints, not third-party signed URLs.

## Before production use

Review authentication and authorisation, token/session handling, rate limits, upload and download paths, database migrations, logging, backups, secret management, transport security, and deployment configuration.
