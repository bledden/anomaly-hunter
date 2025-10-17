"""
ElevenLabs Voice Alert Integration
Generates voice alerts for critical anomalies (severity >= 8)
"""

import os
import requests
from typing import Optional


class ElevenLabsVoice:
    """
    ElevenLabs Voice Alert System

    Converts critical anomaly alerts to voice warnings
    Triggers when severity >= 8/10
    """

    def __init__(self, api_key: Optional[str] = None, voice_id: Optional[str] = None):
        """
        Initialize ElevenLabs client

        Args:
            api_key: ElevenLabs API key (or from env)
            voice_id: Voice ID to use (or from env)
        """
        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY")
        self.voice_id = voice_id or os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")

        if not self.api_key:
            print("[WARN] ELEVENLABS_API_KEY not set - voice alerts disabled")

        self.base_url = "https://api.elevenlabs.io/v1"

    def generate_alert(self, verdict_summary: str, severity: int, confidence: float) -> bool:
        """
        Generate voice alert for critical anomaly

        Args:
            verdict_summary: Summary of the anomaly
            severity: Severity level (1-10)
            confidence: Confidence percentage

        Returns:
            True if alert generated successfully, False otherwise
        """

        if not self.api_key:
            return False

        if severity < 8:
            return False  # Only alert on critical issues

        # Construct alert message
        alert_text = self._construct_alert_message(verdict_summary, severity, confidence)

        try:
            # Call ElevenLabs TTS API
            url = f"{self.base_url}/text-to-speech/{self.voice_id}"

            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.api_key
            }

            data = {
                "text": alert_text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75
                }
            }

            response = requests.post(url, json=data, headers=headers, timeout=30)

            if response.status_code == 200:
                # Save audio file
                output_path = "anomaly_alert.mp3"
                with open(output_path, "wb") as f:
                    f.write(response.content)

                print(f"[VOICE ALERT] 🔊 Critical anomaly alert generated: {output_path}")
                print(f"[VOICE ALERT] Severity {severity}/10 | Confidence {confidence}%")

                # Try to play the audio (macOS)
                try:
                    import subprocess
                    subprocess.run(["afplay", output_path], check=False)
                except Exception:
                    pass  # Audio playback optional

                return True
            else:
                print(f"[ERROR] ElevenLabs API error ({response.status_code}): {response.text}")
                return False

        except Exception as e:
            print(f"[ERROR] Voice alert generation failed: {e}")
            return False

    def _construct_alert_message(self, verdict_summary: str, severity: int, confidence: float) -> str:
        """Construct human-readable alert message"""

        severity_label = "CRITICAL" if severity >= 9 else "HIGH"

        # Extract first sentence or key finding
        summary_lines = verdict_summary.split(".")
        key_finding = summary_lines[0] if summary_lines else verdict_summary

        # Keep it concise for voice
        if len(key_finding) > 200:
            key_finding = key_finding[:197] + "..."

        message = f"""
        Alert! {severity_label} severity anomaly detected.
        Confidence level: {confidence:.0f} percent.
        Finding: {key_finding}.
        Immediate investigation required.
        """

        return message.strip()


# Quick test
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    voice = ElevenLabsVoice()

    test_summary = "Network packet loss spike from 0.1% to 8%. Three anomaly clusters detected indicating cascading infrastructure failure."

    print("\n" + "="*60)
    print("ELEVENLABS VOICE ALERT TEST")
    print("="*60)

    success = voice.generate_alert(
        verdict_summary=test_summary,
        severity=9,
        confidence=95.0
    )

    print(f"\nAlert generated: {'✅ Yes' if success else '❌ No'}")
    print("="*60)
