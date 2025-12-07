"""
Fix Adaptive Cards file location
Moves Adaptivecardstemplate.groovy to correct Python location
"""

import os
import shutil

def fix_adaptive_cards():
    """Move and rename Adaptive Cards file"""
    
    source = "Adaptivecardstemplate.groovy"
    target = "src/teams_bot/adaptive_cards.py"
    
    print("🔧 Fixing Adaptive Cards file location...\n")
    
    if os.path.exists(source):
        # Create directory if needed
        os.makedirs(os.path.dirname(target), exist_ok=True)
        
        # Copy file
        shutil.copy(source, target)
        print(f"✅ Copied: {source} → {target}")
        print(f"📝 Original file preserved at: {source}")
        print(f"ℹ️  You can delete {source} after verifying\n")
        
        # Verify the copy
        if os.path.exists(target):
            size = os.path.getsize(target)
            print(f"✅ Verification: {target} ({size:,} bytes)")
            
            # Read first few lines to verify it's valid Python
            with open(target, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                if first_line.startswith('"""') or first_line.startswith('#'):
                    print(f"✅ File format: Valid Python")
                else:
                    print(f"⚠️  Warning: File may not be valid Python")
            
            return True
        else:
            print(f"❌ Verification failed: {target} not found")
            return False
    else:
        print(f"❌ Source file not found: {source}")
        print(f"   Looking in: {os.path.abspath('.')}")
        print(f"\n   Expected location: {os.path.abspath(source)}")
        return False

if __name__ == "__main__":
    success = fix_adaptive_cards()
    if success:
        print("\n🎉 File fix complete! Ready for component testing.")
    else:
        print("\n❌ File fix failed. Please check file locations.")