"""
Interactive setup script for LLM Deficiency Detector
"""
from dotenv import load_dotenv
import os
import sys

load_dotenv()

def setup():
    print("="*80)
    print("LLM DEFICIENCY DETECTOR - SETUP WIZARD")
    print("="*80)
    print()
    
    # Check if .env exists (in parent directory)
    env_path = "../.env"
    if os.path.exists(env_path):
        print(f"✓ .env file already exists at {env_path}")
        with open(env_path, "r") as f:
            content = f.read()
            if "ANTHROPIC_API_KEY" in content and "your_api_key" not in content:
                print("✓ ANTHROPIC_API_KEY appears to be configured")
                env_ok = True
            else:
                print("⚠ ANTHROPIC_API_KEY not configured in .env")
                env_ok = False
    else:
        print("✗ .env file not found")
        env_ok = False
    
    if not env_ok:
        print()
        print("To get your API key:")
        print("1. Go to https://console.anthropic.com/")
        print("2. Sign up or log in")
        print("3. Navigate to API Keys")
        print("4. Create a new key")
        print()
        
        response = input("Do you have your API key ready? (y/n): ").lower()
        
        if response == 'y':
            api_key = input("Enter your ANTHROPIC_API_KEY: ").strip()
            
            if api_key and api_key.startswith("sk-ant-"):
                with open(env_path, "w") as f:
                    f.write(f"ANTHROPIC_API_KEY={api_key}\n")
                print(f"✓ .env file created successfully at {env_path}")
            else:
                print("⚠ API key doesn't look valid (should start with 'sk-ant-')")
                print("  You can manually edit .env file later")
        else:
            print("Please get your API key and create a .env file in the root directory:")
            print("  echo 'ANTHROPIC_API_KEY=sk-ant-your-key-here' > ../.env")
    
    print()
    print("-"*80)
    
    # Check if CSV exists
    csv_path = "../merged_conditions_with_related_docs__FULL_filtered_simple.csv"
    if os.path.exists(csv_path):
        print(f"✓ Conditions CSV found: {csv_path}")
        
        # Try to count lines
        try:
            with open(csv_path, "r", encoding="utf-8") as f:
                line_count = sum(1 for _ in f) - 1  # Subtract header
            print(f"  Contains {line_count} conditions")
        except:
            print("  (Unable to count conditions)")
    else:
        print(f"✗ Conditions CSV not found: {csv_path}")
        print("  Make sure you have the conditions CSV file in this directory")
    
    print()
    print("-"*80)
    
    # Check dependencies
    print("Checking dependencies...")
    
    missing_deps = []
    
    try:
        import anthropic
        print("✓ anthropic package installed")
    except ImportError:
        print("✗ anthropic package not installed")
        missing_deps.append("anthropic")
    
    try:
        import pandas
        print("✓ pandas package installed")
    except ImportError:
        print("✗ pandas package not installed")
        missing_deps.append("pandas")
    
    try:
        from dotenv import load_dotenv
        print("✓ python-dotenv package installed")
    except ImportError:
        print("✗ python-dotenv package not installed")
        missing_deps.append("python-dotenv")
    
    if missing_deps:
        print()
        print(f"⚠ Missing dependencies: {', '.join(missing_deps)}")
        print()
        response = input("Install missing dependencies now? (y/n): ").lower()
        
        if response == 'y':
            import subprocess
            print("Installing...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_deps)
                print("✓ Dependencies installed successfully!")
            except:
                print("✗ Installation failed. Try manually:")
                print(f"  pip install {' '.join(missing_deps)}")
    
    print()
    print("="*80)
    print("SETUP STATUS")
    print("="*80)
    
    all_ok = True
    
    if env_ok:
        print("✓ API Key configured")
    else:
        print("✗ API Key not configured")
        all_ok = False
    
    if os.path.exists(csv_path):
        print("✓ Conditions CSV present")
    else:
        print("✗ Conditions CSV missing")
        all_ok = False
    
    if not missing_deps:
        print("✓ All dependencies installed")
    else:
        print("✗ Some dependencies missing")
        all_ok = False
    
    print()
    
    if all_ok:
        print("🎉 Setup complete! You're ready to test.")
        print()
        print("Next steps:")
        print("  python test_llm_detector.py          # Run test")
        print("  python compare_approaches.py         # Compare approaches")
        print()
        print("Documentation:")
        print("  LLM_DETECTOR_GUIDE.md               # Complete guide")
        print("  IMPLEMENTATION_SUMMARY.md           # Quick overview")
    else:
        print("⚠ Setup incomplete. Please fix the issues above.")
        print()
        print("Quick fixes:")
        if not env_ok:
            print("  • Add API key to .env file")
        if not os.path.exists(csv_path):
            print(f"  • Add {csv_path} to this directory")
        if missing_deps:
            print("  • Run: pip install -r requirements.txt")
    
    print()
    print("="*80)


if __name__ == "__main__":
    try:
        setup()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled.")
    except Exception as e:
        print(f"\n\n❌ Setup error: {e}")
        import traceback
        traceback.print_exc()



