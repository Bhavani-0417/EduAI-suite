# Security and data handling

EduAI Suite is an evolving portfolio project. It has not undergone an independent security audit and must not be treated as a production-grade document vault or student-record system.

## Important handling rules

- Use synthetic data for demos and development. Do not upload real identity cards, transcripts, marksheets, certificates, or other sensitive personal records to a public deployment.
- Keep \`.env\` files, database dumps, generated documents, uploaded originals, and encrypted vault files out of Git.
- Share URLs contain bearer tokens. Anyone who obtains a valid, unexpired token can download the associated document. Owners can revoke an active share token from the vault UI.
- Vault uploads are capped at 10 MB and limited to PDF, PNG, JPG/JPEG, and BMP. The backend checks file signatures as well as extensions; this is a format sanity check, not malware scanning or full parser validation.
- New OCR text is Fernet-encrypted before it is stored in PostgreSQL. Existing legacy OCR values remain plaintext until the migration command is run.
- Download responses use sanitized filenames, reject path traversal and symlink escapes, and set no-store/nosniff headers.
- Event creation/seeding, college catalog mutations, and college branding updates require an administrator account.
- Generated output files still share one application directory and do not yet have per-user ownership metadata. Path checks prevent traversal, but they do not provide strong cross-user artifact isolation; do not store or serve private real-user exports in a public multi-user deployment until per-user artifact ownership is implemented.
- Voice uploads accept WAV/MP3/M4A/WebM and are limited to 15 MB. Extension and size checks are not a substitute for media decoding in a sandbox or malware scanning.
- Existing generated documents and encrypted blobs already committed to the repository are not removed by \`.gitignore\`. Review their content and provenance. If sensitive material was committed, removing it from the latest tree is not enough; Git history may also need rewriting and credentials may need rotation.

## Vault encryption compatibility

The document-encryption key derivation remains unchanged for compatibility with existing encrypted vault files. It derives a Fernet key from \`SECRET_KEY\` using PBKDF2-HMAC-SHA256, 100,000 iterations, and the existing application salt. OCR data uses a separate purpose-specific salt and a versioned ciphertext prefix.

**Back up the database and encrypted vault directory before running the OCR migration.** From the \`backend/\` directory, with the same \`SECRET_KEY\` and database configuration used by the application, run:

\`\`\`bash
python -m scripts.migrate_vault_ocr
\`\`\`

The migration only transforms legacy plaintext OCR database values; it does not rewrite encrypted files. It skips values already carrying the current ciphertext prefix and can be rerun after an interrupted run. Do not change \`SECRET_KEY\` casually: existing document files and OCR ciphertext may become undecryptable if the derived keys change.

Fernet uses authenticated symmetric encryption; it should not be described as AES-256. Share links are bearer-token application endpoints, not third-party signed URLs.

## Before production use

Review authentication and authorisation, token/session handling, rate limits, malware scanning, file parser isolation, database migrations, logging, backups, secret management, transport security, and deployment configuration.
