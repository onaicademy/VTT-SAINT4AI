"""
VTT Analytics Module
Sends anonymous usage data to Supabase for product improvement.
"""
import os
import sys
import uuid
import json
import platform
import threading
from datetime import datetime

# Optional: requests for HTTP calls
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# Analytics config
ANALYTICS_FILE = "analytics_id.json"
SUPABASE_URL = "https://qiyekjrpcewewxumhifc.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFpeWVranJwY2V3ZXd4dW1oaWZjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjgxNjY4OTYsImV4cCI6MjA4Mzc0Mjg5Nn0.a9E7f2Uox9fDxxty-m2eTfPuiT7iNoSWQwmHl6gk9jE"

# Disable analytics in dev mode
ANALYTICS_ENABLED = True


class VTTAnalytics:
    """Anonymous analytics for VTT."""

    def __init__(self, app_version="2.0"):
        self.app_version = app_version
        self.device_id = self._get_or_create_device_id()
        self.os_name = platform.system().lower()
        self.os_version = platform.version()
        self.session_start = datetime.now()
        self._event_queue = []

    def _get_or_create_device_id(self):
        """Get or create a unique device ID (anonymous)."""
        try:
            if os.path.exists(ANALYTICS_FILE):
                with open(ANALYTICS_FILE, 'r') as f:
                    data = json.load(f)
                    return data.get('device_id')
        except:
            pass

        # Generate new UUID
        device_id = str(uuid.uuid4())
        try:
            with open(ANALYTICS_FILE, 'w') as f:
                json.dump({'device_id': device_id}, f)
        except:
            pass
        return device_id

    def _send_to_supabase(self, table, data):
        """Send data to Supabase (async, non-blocking)."""
        if not ANALYTICS_ENABLED or not HAS_REQUESTS:
            return

        def send():
            try:
                url = f"{SUPABASE_URL}/rest/v1/{table}"
                headers = {
                    "apikey": SUPABASE_ANON_KEY,
                    "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
                    "Content-Type": "application/json",
                    "Prefer": "return=minimal"
                }
                requests.post(url, json=data, headers=headers, timeout=5)
            except Exception as e:
                # Silently fail - analytics should never break the app
                pass

        # Run in background thread
        threading.Thread(target=send, daemon=True).start()

    def track_install(self):
        """Track app installation/first launch."""
        self._send_to_supabase("vtt_installs", {
            "device_id": self.device_id,
            "os": self.os_name,
            "os_version": self.os_version,
            "app_version": self.app_version
        })

    def track_session(self):
        """Track app launch (update last_seen)."""
        # Use upsert via Supabase
        self._send_to_supabase("rpc/track_session", {
            "p_device_id": self.device_id,
            "p_app_version": self.app_version
        })
        # Also send event
        self.track_event("app_launch")

    def track_event(self, event_type, event_data=None):
        """Track any event."""
        self._send_to_supabase("vtt_events", {
            "device_id": self.device_id,
            "event_type": event_type,
            "event_data": event_data or {},
            "app_version": self.app_version
        })

    def track_recording(self, duration_seconds, text_length, language="ru",
                       ai_brain_used=False, success=True, error_message=None):
        """Track a recording/transcription."""
        self._send_to_supabase("vtt_recordings", {
            "device_id": self.device_id,
            "duration_seconds": duration_seconds,
            "text_length": text_length,
            "language": language,
            "ai_brain_used": ai_brain_used,
            "success": success,
            "error_message": error_message
        })

        # Also track as event
        self.track_event("recording_complete", {
            "duration": duration_seconds,
            "text_length": text_length,
            "ai_brain": ai_brain_used,
            "success": success
        })

    def track_error(self, error_type, error_message, stack_trace=None):
        """Track an error for debugging."""
        self._send_to_supabase("vtt_errors", {
            "device_id": self.device_id,
            "error_type": error_type,
            "error_message": error_message,
            "stack_trace": stack_trace,
            "app_version": self.app_version,
            "os": self.os_name
        })

    # Convenience methods for specific events
    def track_recording_start(self):
        self.track_event("recording_start")

    def track_hotkey_used(self, hotkey):
        self.track_event("hotkey_used", {"hotkey": hotkey})

    def track_ai_brain_toggle(self, enabled):
        self.track_event("ai_brain_toggle", {"enabled": enabled})

    def track_settings_changed(self, setting_name, value):
        self.track_event("settings_changed", {"setting": setting_name, "value": str(value)})

    def track_widget_resize(self, new_size):
        self.track_event("widget_resize", {"size": new_size})

    def track_language_switch(self, language):
        self.track_event("language_switch", {"language": language})

    def track_premium_activated(self, license_key_prefix):
        """Track premium activation (only first 4 chars of key for privacy)."""
        self.track_event("premium_activated", {"key_prefix": license_key_prefix[:4]})


# Global analytics instance
_analytics = None

def get_analytics(app_version="2.0"):
    """Get or create global analytics instance."""
    global _analytics
    if _analytics is None:
        _analytics = VTTAnalytics(app_version)
    return _analytics


# Simple function API
def track(event_type, data=None):
    """Simple function to track any event."""
    get_analytics().track_event(event_type, data)
