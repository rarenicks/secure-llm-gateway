import argparse
import sys
import json
import os
from sentinel.factory import GuardrailsFactory
from sentinel.utils import download_spacy_model

def cmd_scan(args):
    """Scan a text string or file."""
    # Load Engine
    try:
        engine = GuardrailsFactory.load(args.profile)
    except Exception as e:
        print(f"Error loading profile '{args.profile}': {e}")
        sys.exit(1)

    # Get Input
    content = ""
    if args.file:
        try:
            with open(args.file, 'r') as f:
                content = f.read()
        except FileNotFoundError:
            print(f"File not found: {args.file}")
            sys.exit(1)
    elif args.text:
        content = args.text
    else:
        # Read from stdin
        if not sys.stdin.isatty():
            content = sys.stdin.read()
        else:
            print("Error: Provide text via --text, --file, or stdin.")
            sys.exit(1)

    # Validate
    result = engine.validate(content)

    # Output
    if args.json:
        output = {
            "valid": result.valid,
            "action": result.action,
            "reason": result.reason,
            "sanitized_text": result.sanitized_text
        }
        print(json.dumps(output, indent=2))
    else:
        status_icon = "✅" if result.valid else "❌"
        if result.action == "redacted":
            status_icon = "⚠️"
        
        print(f"\n{status_icon} Status: {result.action.upper()}")
        if result.reason:
            print(f"📝 Reason: {result.reason}")
        print("-" * 40)
        print(f"Output:\n{result.sanitized_text}")
        print("-" * 40)
        
        if not result.valid and result.action == "blocked":
            sys.exit(1)

def cmd_download(args):
    """Download required models."""
    print("Downloading Spacy models...")
    try:
        download_spacy_model("en_core_web_lg")
        print("✅ Download complete.")
    except Exception as e:
        print(f"❌ Download failed: {e}")
        sys.exit(1)

def cmd_list(args):
    """List available profiles."""
    base_dir = os.path.join(os.path.dirname(__file__), "profiles")
    print(f"Searching in: {base_dir}")
    print("\nAvailable Profiles:")
    for f in os.listdir(base_dir):
        if f.endswith(".yaml"):
            print(f" - {f.replace('.yaml', '')}")

def main():
    parser = argparse.ArgumentParser(description="Semantic Sentinel CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Scan Command
    scan_parser = subparsers.add_parser("scan", help="Scan text or file for security violations")
    scan_parser.add_argument("--text", "-t", type=str, help="Text to scan")
    scan_parser.add_argument("--file", "-f", type=str, help="File to scan")
    scan_parser.add_argument("--profile", "-p", type=str, default="finance", help="Security profile to use (default: finance)")
    scan_parser.add_argument("--json", action="store_true", help="Output in JSON format")
    scan_parser.set_defaults(func=cmd_scan)

    # Download Command
    dl_parser = subparsers.add_parser("setup", help="Download necessary models (Spacy/Presidio)")
    dl_parser.set_defaults(func=cmd_download)
    
    # List Command
    ls_parser = subparsers.add_parser("list", help="List available security profiles")
    ls_parser.set_defaults(func=cmd_list)

    args = parser.parse_args()
    
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
