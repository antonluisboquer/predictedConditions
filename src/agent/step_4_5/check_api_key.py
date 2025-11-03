"""
Quick script to verify API key setup and test connection.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_setup():
    """Check API key configuration."""
    
    print("="*80)
    print("API KEY VERIFICATION")
    print("="*80)
    print()
    
    # load_dotenv() already called at top - it automatically finds .env
    print("✓ load_dotenv() called - .env loaded from project root")
    print()
    
    # Check if API key is loaded
    api_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not api_key:
        print("✗ ANTHROPIC_API_KEY not found in environment")
        print()
        print("Solution:")
        print("  1. Open ../.env file")
        print("  2. Add line: ANTHROPIC_API_KEY=sk-ant-your-key-here")
        print("  3. Get API key from: https://console.anthropic.com/")
        return False
    
    print(f"✓ ANTHROPIC_API_KEY found")
    
    # Check key format
    if api_key.startswith("sk-ant-"):
        print(f"✓ API key format looks correct (starts with 'sk-ant-')")
        print(f"  Key preview: {api_key[:15]}...{api_key[-4:]}")
    else:
        print(f"⚠ API key format looks unusual (should start with 'sk-ant-')")
        print(f"  Current key starts with: {api_key[:10]}...")
    
    print()
    print("-"*80)
    print()
    
    # Test API connection
    print("Testing API connection...")
    try:
        from anthropic import Anthropic
        
        client = Anthropic(api_key=api_key)
        
        # Simple test call
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=50,
            messages=[{"role": "user", "content": "Say 'API test successful' and nothing else."}]
        )
        
        result_text = response.content[0].text
        print(f"✓ API connection successful!")
        print(f"  Claude responded: {result_text}")
        print(f"  Tokens used: {response.usage.input_tokens} in, {response.usage.output_tokens} out")
        
        return True
        
    except ImportError:
        print("✗ anthropic package not installed")
        print()
        print("Solution:")
        print("  pip install anthropic")
        return False
        
    except Exception as e:
        print(f"✗ API connection failed")
        print(f"  Error: {str(e)}")
        print()
        print("Common issues:")
        print("  - Invalid API key")
        print("  - No API credits remaining")
        print("  - Network/firewall issues")
        print("  - API service temporarily down")
        print()
        print("Verify at: https://console.anthropic.com/")
        return False


if __name__ == "__main__":
    success = check_setup()
    
    print()
    print("="*80)
    
    if success:
        print("✅ ALL CHECKS PASSED")
        print()
        print("You're ready to run:")
        print("  python test_llm_detector.py")
    else:
        print("❌ SETUP INCOMPLETE")
        print()
        print("Fix the issues above, then run this script again")
    
    print("="*80)

