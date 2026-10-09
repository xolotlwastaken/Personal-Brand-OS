"""Native Hermes stdio chat, with public/redacted output only. No listener ports."""
import os

# Root is transport infrastructure. Every chat explicitly selects a named profile.
os.environ['HERMES_HOME'] = '/opt/data'
os.environ.pop('HERMES_PROFILE', None)

from agent.redact import redact_sensitive_text
from tui_gateway import entry


def visible(value):
    if isinstance(value, str):
        return redact_sensitive_text(value, force=True)
    if isinstance(value, dict):
        return {k: ('[REDACTED]' if k.lower() in {'api_key', 'authorization', 'cookie', 'password',
                                                'access_token', 'refresh_token', 'secret'} else visible(v))
                for k, v in value.items()
                if k not in {'reasoning', 'reasoning_content', 'last_reasoning', 'rendered'}}
    if isinstance(value, list):
        return [visible(v) for v in value]
    return value


class PublicTransport:
    def __init__(self, original):
        self.original = original

    def write(self, frame):
        if frame.get('method') == 'event':
            kind = frame.get('params', {}).get('type', '')
            if kind.startswith(('reasoning.', 'thinking.')):
                return True
        return self.original.write(visible(frame))

    def close(self):
        return self.original.close()


if __name__ == '__main__':
    entry.server._stdio_transport = PublicTransport(entry.server._stdio_transport)
    entry.main()
