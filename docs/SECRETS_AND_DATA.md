# Secrets And Data Policy

The project is designed for public code and private data.

Never commit:

- raw PDFs
- page images
- OCR output
- extracted page text
- parsed commercial monster data
- private exports or reports
- database dumps
- `.env` files or credentials

Allowed in Git:

- source code
- architecture and implementation docs
- synthetic fixtures
- SRD/CC-BY fixtures with clear provenance
- derived public examples that do not reproduce copyrighted text

All parser tests should begin with synthetic fixtures. SRD/CC-BY samples may be added
only when their source and license are documented beside the fixture.
