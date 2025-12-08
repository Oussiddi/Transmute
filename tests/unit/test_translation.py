#!/usr/bin/env python3
"""Quick test of Claude translation quality."""

import sys
from pathlib import Path
sys.path.insert(0, "src")

from transmute.llm import ClaudeClient

# Real Python code from the patterns repo
python_code = """
class Borg:
    '''
    The Borg design pattern - all instances share the same state.
    
    This is useful when you want multiple instances to share data
    but don't want to use a Singleton.
    '''
    _shared_state = {}

    def __init__(self):
        self.__dict__ = self._shared_state

    def __str__(self):
        return str(self.__dict__)


class YourBorg(Borg):
    '''Example subclass of Borg.'''
    
    def __init__(self, state=None):
        super().__init__()
        if state:
            self.state = state
        else:
            if not hasattr(self, 'state'):
                self.state = 'Init'

    def __str__(self):
        return f'YourBorg with state: {self.state}'


def main():
    '''Demonstrate the Borg pattern.'''
    rm1 = YourBorg()
    rm2 = YourBorg()

    rm1.state = 'Idle'
    rm2.state = 'Running'

    print(f'rm1: {rm1}')
    print(f'rm2: {rm2}')
    
    # Both should have 'Running' state
    rm3 = YourBorg()
    print(f'rm3: {rm3}')


if __name__ == '__main__':
    main()
"""

print("=" * 80)
print("🚀 TRANSMUTE - Translation Quality Test")
print("=" * 80)
print()
print("📝 Source Code (Python - Borg Pattern):")
print("-" * 80)
print(python_code[:300] + "...\n")

print("🤖 Translating with Claude Sonnet 4...")
print()

try:
    # Translate with Claude
    client = ClaudeClient()
    
    result = client.translate_code(
        source_code=python_code,
        source_language="python",
        target_language="java"
    )
    
    print("=" * 80)
    print("✅ TRANSLATED JAVA CODE:")
    print("=" * 80)
    print(result['translated_code'])
    print()
    print("=" * 80)
    print(f"📊 Confidence Score: {result['confidence']:.0%}")
    print(f"💡 Explanation: {result['explanation']}")
    print("=" * 80)
    
    # Save to file
    output_file = Path("translation_example.java")
    output_file.write_text(result['translated_code'])
    print(f"\n💾 Saved to: {output_file.absolute()}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()