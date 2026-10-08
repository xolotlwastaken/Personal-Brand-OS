# Optional build; Compose uses the exact official image directly.
# Preserve the official entrypoint and s6 process supervision.
FROM nousresearch/hermes-agent@sha256:9774f4f39a9bb8c2f68ce728ed5e99ddbad282163be56764afacf88ed952b784
LABEL org.opencontainers.image.title="Personal Brand OS"
