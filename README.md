# envoy-cli

> A CLI tool for managing and syncing `.env` files across local and remote environments with secret masking.

---

## Installation

```bash
pip install envoy-cli
```

Or with pipx for isolated installs:

```bash
pipx install envoy-cli
```

---

## Usage

```bash
# Initialize envoy in your project
envoy init

# Push your local .env to a remote environment
envoy push --env production

# Pull remote variables to your local .env
envoy pull --env staging

# List all variables with secrets masked
envoy list --mask-secrets

# Sync between two environments
envoy sync --from staging --to production
```

Example output:

```
$ envoy list --mask-secrets

  KEY                  VALUE
  DATABASE_URL         postgres://user:****@host:5432/db
  API_KEY              ****-****-****-a3f9
  DEBUG                true
```

---

## Configuration

Envoy reads from a `.envoy.toml` file in your project root. Run `envoy init` to generate one automatically.

---

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

---

## License

[MIT](LICENSE) © 2024 envoy-cli contributors