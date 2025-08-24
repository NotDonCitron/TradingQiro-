#!/usr/bin/env python3
"""
Standalone Console Problem Fixer for Cryptet Trading Bot
A comprehensive script to diagnose and fix console problems
"""

import asyncio
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class ConsoleProblemFixer:
    """Main class for fixing console problems"""

    def __init__(self):
        self.diagnostic_engine = None
        self.error_resolver = None
        self.start_time = datetime.utcnow()

    async def initialize(self):
        """Initialize the diagnostic and resolution systems"""
        try:
            from src.utils.console_diagnostics import ConsoleDiagnosticEngine
            from src.utils.error_resolver import ErrorResolver

            self.diagnostic_engine = ConsoleDiagnosticEngine()
            self.error_resolver = ErrorResolver()

            print("✅ Console Problem Fixer initialized successfully")
            return True

        except ImportError as e:
            print(f"❌ Failed to import required modules: {e}")
            print("💡 Make sure you're running this from the project root directory")
            return False
        except Exception as e:
            print(f"❌ Initialization error: {e}")
            return False

    async def run_full_diagnostic_and_fix(self) -> Dict[str, Any]:
        """Run full diagnostic and attempt to fix all issues"""
        print("🔧 Cryptet Trading Bot - Console Problem Fixer")
        print("=" * 60)

        if not await self.initialize():
            return {"status": "error", "message": "Failed to initialize"}

        try:
            print(f"🕐 Starting diagnostics at {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print()

            # Step 1: Run diagnostics
            print("📋 STEP 1: Running System Diagnostics")
            print("-" * 40)

            if not self.diagnostic_engine:
                raise RuntimeError("Diagnostic engine not initialized")

            diagnostic_results = await self.diagnostic_engine.run_full_diagnosis()

            # Step 2: Analyze results
            print("\n📊 STEP 2: Analyzing Diagnostic Results")
            print("-" * 40)

            critical_issues = [r for r in diagnostic_results if r.status == "critical"]
            error_issues = [r for r in diagnostic_results if r.status == "error"]
            warning_issues = [r for r in diagnostic_results if r.status == "warning"]
            ok_issues = [r for r in diagnostic_results if r.status == "ok"]

            print(f"📈 Diagnostic Summary:")
            print(f"   ✅ OK: {len(ok_issues)} checks passed")
            print(f"   ⚠️  Warnings: {len(warning_issues)}")
            print(f"   ❌ Errors: {len(error_issues)}")
            print(f"   🚨 Critical: {len(critical_issues)}")

            if critical_issues or error_issues:
                print("\n🔧 STEP 3: Attempting Automatic Resolution")
                print("-" * 40)

                # Attempt to resolve issues
                if not self.error_resolver:
                    raise RuntimeError("Error resolver not initialized")

                resolution_results = await self.error_resolver.resolve_diagnostic_results(diagnostic_results)

                successful_resolutions = [r for r in resolution_results if r.success]
                failed_resolutions = [r for r in resolution_results if not r.success]

                print(f"📈 Resolution Summary:")
                print(f"   ✅ Successful: {len(successful_resolutions)} fixes applied")
                print(f"   ❌ Failed: {len(failed_resolutions)} fixes couldn't be applied")

                if successful_resolutions:
                    print("\n✅ Successfully Applied Fixes:")
                    for resolution in successful_resolutions:
                        print(f"   • {resolution.message}")

                if failed_resolutions:
                    print("\n❌ Unresolved Issues (require manual intervention):")
                    for resolution in failed_resolutions:
                        print(f"   • {resolution.message}")

                # Re-run diagnostics to verify fixes
                print("\n🔄 STEP 4: Verifying Fixes")
                print("-" * 40)

                print("Re-running diagnostics to verify fixes...")
                verification_results = await self.diagnostic_engine.run_full_diagnosis()

                verification_critical = [r for r in verification_results if r.status == "critical"]
                verification_errors = [r for r in verification_results if r.status == "error"]

                if len(verification_critical) < len(critical_issues) or len(verification_errors) < len(error_issues):
                    improvement = (len(critical_issues) + len(error_issues)) - (len(verification_critical) + len(verification_errors))
                    print(f"✅ Improvement detected: {improvement} issues resolved")
                else:
                    print("ℹ️  No significant improvement detected")

            else:
                print("\n✅ No issues requiring resolution found!")
                resolution_results = []

            # Generate final report
            end_time = datetime.utcnow()
            duration = (end_time - self.start_time).total_seconds()

            report = {
                "timestamp": end_time.isoformat() + "Z",
                "duration_seconds": round(duration, 2),
                "status": "completed",
                "diagnostics": self.diagnostic_engine.generate_report() if self.diagnostic_engine else {},
                "resolutions": self.error_resolver.generate_resolution_report() if self.error_resolver else {}
            }

            # Save detailed report
            report_file = f"console_fix_report_{end_time.strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w') as f:
                import json
                json.dump(report, f, indent=2)

            print(f"\n📄 Detailed report saved to: {report_file}")

            return report

        except KeyboardInterrupt:
            print("\n🛑 Operation interrupted by user")
            return {"status": "interrupted"}
        except Exception as e:
            print(f"\n❌ Unexpected error: {str(e)}")
            return {"status": "error", "message": str(e)}

    async def show_help(self):
        """Show help information"""
        print("🔧 Cryptet Trading Bot - Console Problem Fixer")
        print("=" * 60)
        print()
        print("This script automatically detects and fixes common console problems")
        print("including environment configuration, dependency issues, and connection problems.")
        print()
        print("Usage:")
        print("  python scripts/fix_console_problems.py")
        print()
        print("What it checks:")
        print("  • Environment variables and configuration")
        print("  • Required Python dependencies")
        print("  • Database connectivity")
        print("  • Telegram API configuration")
        print("  • BingX API connectivity")
        print("  • Port availability")
        print("  • File permissions")
        print("  • Log configuration")
        print("  • Memory resources")
        print("  • Network connectivity")
        print()
        print("Automatic fixes:")
        print("  • Creates missing .env files")
        print("  • Installs missing Python packages")
        print("  • Fixes invalid log levels")
        print("  • Creates missing log directories")
        print()
        print("Manual intervention may be required for:")
        print("  • Telegram API credentials")
        print("  • BingX API credentials")
        print("  • Port conflicts")
        print("  • File permission issues")
        print("  • Network configuration")

    async def interactive_mode(self):
        """Run in interactive mode with user prompts"""
        print("🔧 Interactive Console Problem Fixer")
        print("=" * 60)

        if not await self.initialize():
            return

        while True:
            print("\nSelect an option:")
            print("1. Run full diagnostic and fix")
            print("2. Run diagnostics only")
            print("3. Show system information")
            print("4. Help")
            print("5. Exit")

            choice = input("\nEnter your choice (1-5): ").strip()

            if choice == "1":
                await self.run_full_diagnostic_and_fix()
            elif choice == "2":
                if self.diagnostic_engine:
                    print("\n📋 Running diagnostics...")
                    results = await self.diagnostic_engine.run_full_diagnosis()
                    self.diagnostic_engine.print_summary()
                else:
                    print("❌ Diagnostic engine not available")
            elif choice == "3":
                print("\n💻 System Information:")
                print(f"   Python: {sys.version}")
                print(f"   Platform: {sys.platform}")
                print(f"   Working Directory: {os.getcwd()}")
                print(f"   Project Root: {project_root}")
                print(f"   Environment File: {os.path.exists('.env')}")
            elif choice == "4":
                await self.show_help()
            elif choice == "5":
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please select 1-5.")

async def main():
    """Main entry point"""
    fixer = ConsoleProblemFixer()

    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] in ["--help", "-h"]:
            await fixer.show_help()
        elif sys.argv[1] == "--interactive":
            await fixer.interactive_mode()
        elif sys.argv[1] == "--diagnostics-only":
            if await fixer.initialize() and fixer.diagnostic_engine:
                results = await fixer.diagnostic_engine.run_full_diagnosis()
                fixer.diagnostic_engine.print_summary()
            else:
                print("❌ Could not initialize diagnostic engine")
                sys.exit(1)
        else:
            print(f"❌ Unknown option: {sys.argv[1]}")
            print("Use --help for usage information")
            sys.exit(1)
    else:
        # Run full diagnostic and fix by default
        report = await fixer.run_full_diagnostic_and_fix()

        # Exit with appropriate code
        if report.get("status") == "completed":
            diagnostics = report.get("diagnostics", {})
            critical_count = diagnostics.get("issue_counts", {}).get("critical", 0)
            error_count = diagnostics.get("issue_counts", {}).get("error", 0)

            if critical_count > 0:
                print("❌ Critical issues remain. Manual intervention required.")
                sys.exit(1)
            elif error_count > 0:
                print("⚠️  Some errors remain. System may work with limitations.")
                sys.exit(0)
            else:
                print("✅ All checks passed. System appears ready.")
                sys.exit(0)
        else:
            sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        sys.exit(1)
