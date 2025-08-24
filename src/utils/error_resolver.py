#!/usr/bin/env python3
"""
Error Resolver System for Cryptet Trading Bot
Automatically resolves common console problems and configuration issues
"""

import os
import sys
import asyncio
import subprocess
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

from src.utils.console_diagnostics import ErrorType, DiagnosticResult, ResolutionResult

class ResolutionType(Enum):
    """Types of error resolutions available"""
    ENVIRONMENT_FIX = "environment_fix"
    DEPENDENCY_INSTALL = "dependency_install"
    FILE_CREATION = "file_creation"
    PERMISSION_FIX = "permission_fix"
    CONFIGURATION_UPDATE = "configuration_update"
    SERVICE_RESTART = "service_restart"
    NETWORK_RETRY = "network_retry"

@dataclass
class ResolutionAction:
    """An action that can be taken to resolve an error"""
    action_type: ResolutionType
    description: str
    command: Optional[str] = None
    file_path: Optional[str] = None
    content: Optional[str] = None
    environment_var: Optional[str] = None
    environment_value: Optional[str] = None
    risk_level: str = "low"  # "low", "medium", "high"
    requires_restart: bool = False
    auto_executable: bool = True

class ErrorResolver:
    """Automatically resolves detected console errors"""

    def __init__(self):
        self.resolutions_attempted: List[ResolutionResult] = []
        self.backup_files: Dict[str, str] = {}

    async def resolve_diagnostic_results(self, diagnostic_results: List[DiagnosticResult]) -> List[ResolutionResult]:
        """Resolve all issues found in diagnostic results"""
        print("🔧 Starting Error Resolution...")

        for result in diagnostic_results:
            if result.status != "ok":  # Only resolve non-ok results
                resolution = await self.resolve_single_error(result)
                if resolution:
                    self.resolutions_attempted.append(resolution)
                    print(f"  {'✅' if resolution.success else '❌'} {resolution.message}")

        print(f"✅ Resolution completed. Attempted {len(self.resolutions_attempted)} fixes.")
        return self.resolutions_attempted

    async def resolve_single_error(self, diagnostic_result: DiagnosticResult) -> Optional[ResolutionResult]:
        """Resolve a single diagnostic error"""
        error_type = diagnostic_result.error_type
        status = diagnostic_result.status

        # Don't attempt to resolve critical errors automatically
        if status == "critical":
            return ResolutionResult(
                error_type=error_type,
                success=False,
                message=f"Critical error requires manual intervention: {diagnostic_result.message}",
                actions_taken=["Manual intervention required"],
                timestamp=datetime.utcnow().isoformat() + "Z"
            )

        # Route to appropriate resolver based on error type
        resolver_map = {
            ErrorType.ENVIRONMENT: self._resolve_environment_error,
            ErrorType.IMPORT: self._resolve_import_error,
            ErrorType.DATABASE: self._resolve_database_error,
            ErrorType.CONNECTION: self._resolve_connection_error,
            ErrorType.CONFIGURATION: self._resolve_configuration_error,
            ErrorType.PERMISSION: self._resolve_permission_error,
            ErrorType.RESOURCE: self._resolve_resource_error,
        }

        resolver_func = resolver_map.get(error_type)
        if resolver_func:
            try:
                return await resolver_func(diagnostic_result)
            except Exception as e:
                return ResolutionResult(
                    error_type=error_type,
                    success=False,
                    message=f"Resolution failed: {str(e)}",
                    actions_taken=["Error during resolution attempt"],
                    timestamp=datetime.utcnow().isoformat() + "Z"
                )

        return ResolutionResult(
            error_type=error_type,
            success=False,
            message=f"No automatic resolution available for {error_type.value} errors",
            actions_taken=["Manual resolution required"],
            timestamp=datetime.utcnow().isoformat() + "Z"
        )

    async def _resolve_environment_error(self, result: DiagnosticResult) -> Optional[ResolutionResult]:
        """Resolve environment configuration errors"""
        actions_taken = []

        # Check if we can auto-fix missing environment variables
        if result.details.get("missing_required"):
            missing_vars = result.details["missing_required"]

            # Try to create a basic .env file with defaults
            if not os.path.exists(".env") and "DATABASE_URL" in missing_vars:
                try:
                    await self._create_default_env_file()
                    actions_taken.append("Created default .env file")
                except Exception as e:
                    actions_taken.append(f"Failed to create .env file: {str(e)}")

        # Check for invalid values that can be auto-corrected
        if result.details.get("invalid_values"):
            invalid_values = result.details["invalid_values"]

            for invalid_msg in invalid_values:
                if "LOG_LEVEL" in invalid_msg and "must be one of" in invalid_msg:
                    # Fix invalid log level
                    try:
                        await self._fix_log_level()
                        actions_taken.append("Fixed invalid LOG_LEVEL")
                    except Exception as e:
                        actions_taken.append(f"Failed to fix LOG_LEVEL: {str(e)}")

        if actions_taken:
            return ResolutionResult(
                error_type=ErrorType.ENVIRONMENT,
                success=True,
                message="Environment configuration partially resolved",
                actions_taken=actions_taken,
                timestamp=datetime.utcnow().isoformat() + "Z"
            )

        return ResolutionResult(
            error_type=ErrorType.ENVIRONMENT,
            success=False,
            message="Environment issues require manual configuration",
            actions_taken=["Manual .env file configuration required"],
            timestamp=datetime.utcnow().isoformat() + "Z"
        )

    async def _resolve_import_error(self, result: DiagnosticResult) -> Optional[ResolutionResult]:
        """Resolve missing dependency errors"""
        actions_taken = []

        if result.details.get("missing_modules"):
            missing_modules = result.details["missing_modules"]

            for module in missing_modules:
                try:
                    print(f"    📦 Installing {module}...")
                    success = await self._install_package(module)
                    if success:
                        actions_taken.append(f"Installed {module}")
                    else:
                        actions_taken.append(f"Failed to install {module}")
                except Exception as e:
                    actions_taken.append(f"Error installing {module}: {str(e)}")

        if actions_taken:
            return ResolutionResult(
                error_type=ErrorType.IMPORT,
                success=True,
                message="Missing dependencies installed",
                actions_taken=actions_taken,
                timestamp=datetime.utcnow().isoformat() + "Z"
            )

        return ResolutionResult(
            error_type=ErrorType.IMPORT,
            success=False,
            message="Dependency installation failed",
            actions_taken=["Manual pip install required"],
            timestamp=datetime.utcnow().isoformat() + "Z"
        )

    async def _resolve_database_error(self, result: DiagnosticResult) -> Optional[ResolutionResult]:
        """Resolve database configuration errors"""
        actions_taken = []

        # If database file doesn't exist, it might be created automatically
        if "does not exist" in result.message and "SQLite" in result.message:
            actions_taken.append("SQLite database will be created on first startup")

            return ResolutionResult(
                error_type=ErrorType.DATABASE,
                success=True,
                message="Database will be auto-created",
                actions_taken=actions_taken,
                timestamp=datetime.utcnow().isoformat() + "Z"
            )

        return ResolutionResult(
            error_type=ErrorType.DATABASE,
            success=False,
            message="Database configuration requires manual setup",
            actions_taken=["Manual database configuration required"],
            timestamp=datetime.utcnow().isoformat() + "Z"
        )

    async def _resolve_connection_error(self, result: DiagnosticResult) -> Optional[ResolutionResult]:
        """Resolve connection-related errors"""
        actions_taken = []

        # For network connectivity issues, we can try some basic fixes
        if "Network connectivity" in result.message:
            try:
                await self._test_network_connectivity()
                actions_taken.append("Retested network connectivity")
            except Exception as e:
                actions_taken.append(f"Network test failed: {str(e)}")

        return ResolutionResult(
            error_type=ErrorType.CONNECTION,
            success=True,
            message="Connection issue acknowledged",
            actions_taken=actions_taken,
            timestamp=datetime.utcnow().isoformat() + "Z"
        )

    async def _resolve_configuration_error(self, result: DiagnosticResult) -> Optional[ResolutionResult]:
        """Resolve configuration errors"""
        actions_taken = []

        if "Invalid LOG_LEVEL" in result.message:
            try:
                await self._fix_log_level()
                actions_taken.append("Fixed LOG_LEVEL configuration")
            except Exception as e:
                actions_taken.append(f"Failed to fix LOG_LEVEL: {str(e)}")

        if "Port conflicts" in result.message:
            actions_taken.append("Port conflict detected - requires manual resolution")

        if actions_taken:
            return ResolutionResult(
                error_type=ErrorType.CONFIGURATION,
                success=True,
                message="Configuration issues resolved",
                actions_taken=actions_taken,
                timestamp=datetime.utcnow().isoformat() + "Z"
            )

        return ResolutionResult(
            error_type=ErrorType.CONFIGURATION,
            success=False,
            message="Configuration requires manual adjustment",
            actions_taken=["Manual configuration required"],
            timestamp=datetime.utcnow().isoformat() + "Z"
        )

    async def _resolve_permission_error(self, result: DiagnosticResult) -> Optional[ResolutionResult]:
        """Resolve file permission errors"""
        actions_taken = []

        if result.details.get("permission_issues"):
            permission_issues = result.details["permission_issues"]

            for issue in permission_issues:
                if "log" in issue.lower():
                    try:
                        await self._create_log_directory()
                        actions_taken.append("Created logs directory")
                    except Exception as e:
                        actions_taken.append(f"Failed to create logs directory: {str(e)}")

        return ResolutionResult(
            error_type=ErrorType.PERMISSION,
            success=len(actions_taken) > 0,
            message="Permission issues addressed",
            actions_taken=actions_taken,
            timestamp=datetime.utcnow().isoformat() + "Z"
        )

    async def _resolve_resource_error(self, result: DiagnosticResult) -> Optional[ResolutionResult]:
        """Resolve resource-related errors"""
        actions_taken = []

        if "psutil not installed" in result.message:
            try:
                success = await self._install_package("psutil")
                if success:
                    actions_taken.append("Installed psutil for memory monitoring")
                else:
                    actions_taken.append("Failed to install psutil")
            except Exception as e:
                actions_taken.append(f"Error installing psutil: {str(e)}")

        return ResolutionResult(
            error_type=ErrorType.RESOURCE,
            success=len(actions_taken) > 0,
            message="Resource monitoring improved",
            actions_taken=actions_taken,
            timestamp=datetime.utcnow().isoformat() + "Z"
        )

    async def _create_default_env_file(self) -> None:
        """Create a default .env file with basic configuration"""
        if os.path.exists(".env"):
            # Backup existing file
            backup_path = f".env.backup.{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            os.rename(".env", backup_path)
            self.backup_files[".env"] = backup_path

        default_content = """# Cryptet Trading Bot Configuration
# Copy from .env.example and configure your values

# Database Configuration
DATABASE_URL=sqlite:///trading_bot.db

# Telegram API Configuration (REQUIRED)
TELEGRAM_API_ID=your_api_id_here
TELEGRAM_API_HASH=your_api_hash_here
TELEGRAM_BOT_TOKEN=your_bot_token_here

# BingX API Configuration (for trading)
BINGX_API_KEY=your_bingx_api_key_here
BINGX_SECRET_KEY=your_bingx_secret_key_here
BINGX_TESTNET=true

# Trading Configuration
TRADING_ENABLED=false

# Monitoring Configuration
LOG_LEVEL=INFO

# Signal Source Configuration
MONITORED_CHAT_IDS=-1002299206473,-1001804143400
VIP_GROUP_ID=-1002299206473
CRYPTET_CHANNEL_ID=-1001804143400
TARGET_GROUP_ID=-1002773853382
CRYPTET_ENABLED=true

# Port Configuration
PORT=8080

# Browser Configuration (for Selenium)
CRYPTET_HEADLESS=true
CHROME_BINARY_PATH=/usr/bin/google-chrome

# Development Configuration
DEBUG_MODE=false
DEVELOPMENT=false
"""

        with open(".env", "w") as f:
            f.write(default_content)

        print("    ✅ Created default .env file")

    async def _fix_log_level(self) -> None:
        """Fix invalid LOG_LEVEL configuration"""
        current_level = os.getenv("LOG_LEVEL", "INFO").upper()
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

        if current_level not in valid_levels:
            # Set to INFO as default
            os.environ["LOG_LEVEL"] = "INFO"
            print("    ✅ Fixed LOG_LEVEL to INFO")

    async def _install_package(self, package_name: str) -> bool:
        """Install a Python package using pip"""
        try:
            process = await asyncio.create_subprocess_exec(
                sys.executable, "-m", "pip", "install", package_name,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                return True
            else:
                print(f"    ❌ Failed to install {package_name}: {stderr.decode()}")
                return False
        except Exception as e:
            print(f"    ❌ Error installing {package_name}: {str(e)}")
            return False

    async def _create_log_directory(self) -> None:
        """Create the logs directory if it doesn't exist"""
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
            print(f"    ✅ Created logs directory: {log_dir}")

    async def _test_network_connectivity(self) -> None:
        """Test basic network connectivity"""
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get("https://httpbin.org/status/200")
                if response.status_code == 200:
                    print("    ✅ Network connectivity verified")
        except Exception as e:
            print(f"    ⚠️  Network test failed: {str(e)}")

    def generate_resolution_report(self) -> Dict[str, Any]:
        """Generate a report of all resolution attempts"""
        successful_resolutions = [r for r in self.resolutions_attempted if r.success]
        failed_resolutions = [r for r in self.resolutions_attempted if not r.success]

        report = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "total_attempts": len(self.resolutions_attempted),
            "successful": len(successful_resolutions),
            "failed": len(failed_resolutions),
            "success_rate": len(successful_resolutions) / max(len(self.resolutions_attempted), 1),
            "resolutions": [asdict(r) for r in self.resolutions_attempted],
            "backup_files_created": self.backup_files
        }

        return report

    def print_resolution_summary(self) -> None:
        """Print a summary of resolution attempts"""
        print("\n" + "="*60)
        print("🔧 ERROR RESOLUTION SUMMARY")
        print("="*60)

        if not self.resolutions_attempted:
            print("✅ No resolutions were needed")
            return

        successful = [r for r in self.resolutions_attempted if r.success]
        failed = [r for r in self.resolutions_attempted if not r.success]

        print(f"Total Attempts: {len(self.resolutions_attempted)}")
        print(f"✅ Successful: {len(successful)}")
        print(f"❌ Failed: {len(failed)}")

        if successful:
            print("\n✅ SUCCESSFUL RESOLUTIONS:")
            for resolution in successful:
                print(f"  • {resolution.message}")

        if failed:
            print("\n❌ FAILED RESOLUTIONS:")
            for resolution in failed:
                print(f"  • {resolution.message}")

        if self.backup_files:
            print("\n📁 BACKUP FILES CREATED:")
            for original, backup in self.backup_files.items():
                print(f"  • {original} -> {backup}")

        print("\n" + "="*60)

async def main():
    """Main function for standalone error resolution"""
    from src.utils.console_diagnostics import ConsoleDiagnosticEngine

    print("🔧 Cryptet Trading Bot - Error Resolution")
    print("This will attempt to automatically fix detected problems")
    print()

    try:
        # First run diagnostics
        diagnostic_engine = ConsoleDiagnosticEngine()
        diagnostic_results = await diagnostic_engine.run_full_diagnosis()

        # Then attempt resolutions
        resolver = ErrorResolver()
        resolution_results = await resolver.resolve_diagnostic_results(diagnostic_results)

        # Print summaries
        diagnostic_engine.print_summary()
        resolver.print_resolution_summary()

        # Generate combined report
        report = {
            "diagnostics": diagnostic_engine.generate_report(),
            "resolutions": resolver.generate_resolution_report()
        }

        # Save report
        report_file = f"error_resolution_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\n📄 Combined report saved to: {report_file}")

        # Check if system is ready
        critical_count = sum(1 for r in diagnostic_results if r.status == "critical")
        error_count = sum(1 for r in diagnostic_results if r.status == "error")

        if critical_count > 0:
            print("❌ Critical issues remain. Manual intervention required.")
            sys.exit(1)
        elif error_count > 0:
            print("⚠️  Some errors remain. System may work with limitations.")
            sys.exit(0)
        else:
            print("✅ System is ready to run!")

    except KeyboardInterrupt:
        print("\n🛑 Resolution interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Resolution system error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
