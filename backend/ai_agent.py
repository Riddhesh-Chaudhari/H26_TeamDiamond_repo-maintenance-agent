
import json
import urllib.error
import urllib.request


OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "qwen2.5-coder:7b"


def analyze_maintenance_evidence(evidence: str) -> dict:
    """Ask the local AI model to analyze supplied maintenance evidence."""

    prompt = f"""
You are an assistant for an open-source repository maintenance tool.

Analyze only the evidence supplied below.
Do not invent vulnerabilities, package versions, or test results.
Separate observed facts from recommendations.
If the evidence is insufficient, say so.
Do not claim that a proposed fix has been verified.

Return a JSON object with these keys:
- issue
- evidence
- analysis
- recommended_action
- compatibility_concerns
- limitations
- verification_status

Set verification_status to "not_verified".

Repository evidence:
{evidence}
"""

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "user",
                "content": prompt,
            }
        ],
        "stream": False,
        "format": "json",
    }

    request = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            result = json.loads(response.read().decode("utf-8"))

        content = result["message"]["content"]
        analysis = json.loads(content)

        required_keys = {
            "issue",
            "evidence",
            "analysis",
            "recommended_action",
            "compatibility_concerns",
            "limitations",
            "verification_status",
        }

        if not isinstance(analysis, dict) or not required_keys.issubset(analysis):
            raise ValueError("AI response is missing required fields.")

        # The model cannot certify that a fix was tested.
        analysis["verification_status"] = "not_verified"
        return analysis

    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError(
            "Could not contact Ollama. Check that it is running."
        ) from exc
    except (json.JSONDecodeError, KeyError, ValueError) as exc:
        raise RuntimeError(
            "Ollama returned an invalid or incomplete JSON response."
        ) from exc


if __name__ == "__main__":
    sample_evidence = """
Source: observed evidence from the LinkWatch repository.

Repository: LinkWatch

Finding: Runtime dependency compatibility failure involving Jinja2 and MarkupSafe.

Dependency declarations:
- requirements.txt pins Jinja2==2.11.3.
- pyproject.toml pins Jinja2==2.11.3.
- Neither dependency file directly pins MarkupSafe.

Baseline test results:
- Installed Jinja2 version: 2.11.3.
- Installed MarkupSafe version: 3.0.4.
- Tests: 9 passed, 1 failed.
- Failure: ImportError: cannot import name 'soft_unicode' from 'markupsafe'.

Diagnostic experiment:
- Installed MarkupSafe==2.0.1 in the isolated environment.
- Tests afterward: 10 passed, 0 failed.
- pip check reported no broken requirements.

Limitations:
- No project source or dependency files have been changed.
- A clean installation has not been tested.
- Compatibility across Python versions has not been verified.
- The diagnostic experiment is not yet a permanent fix.

Do not claim that the dependency is vulnerable.
Distinguish observed results from recommendations.
Mark the analysis as not verified beyond the supplied evidence.
"""

    report = analyze_maintenance_evidence(sample_evidence)
    print(json.dumps(report, indent=2))
