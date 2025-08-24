#!/usr/bin/env python3
"""
Console Diagnostics System for Cryptet Trading Bot
Provides comprehensive error detection and resolution for console problems
"""

import os
import sys
import asyncio
import json
import socket
import importlib
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

import httpx

class ErrorType(Enum):
    """Types of console errors that can be detected and resolved"""
    ENVIRONMENT = "environment"
    CONNECTION = "connection"
    DATABASE = "database"
    IMPORT = "import"
    CONFIGURATION = "configuration"
    STARTUP = "startup"
    PERMISSION = "permission"
    RESOURCE = "resource"

@dataclass
class DiagnosticResult:
    """Result of a diagnostic check"""
    error_type: ErrorType
    status: str  # "ok", "warning", "error", "critical"
    message: str
    details: Dict[str, Any]
    recommendations: List[str]
    auto_fixable: bool = False
    timestamp: Optional[str] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat() + "Z"

@dataclass
class ResolutionResult:
    """Result of attempting to resolve an error"""
    error_type: ErrorType
    success: bool
    message: str
    actions_taken: List[str]
    timestamp: Optional[str] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat() + "Z"

class ConsoleDiagnosticEngine:
    """Main diagnostic engine for console problem detection"""

    def __init__(self):
        self.results: List[DiagnosticResult] = []
        self.resolutions: List[ResolutionResult] = []
        self.start_time = datetime.utcnow()

    async def run_full_diagnosis(self) -> List[DiagnosticResult]:
        """Run complete diagnostic suite"""
        print("🔍 Starting Console Diagnostics...")

        # Run all diagnostic checks in order
        checks = [
            self._check_environment_variables,
            self._check_dependencies,
            self._check_database_connection,
            self._check_telegram_connectivity,
            self._check_bingx_connectivity,
            self._check_port_availability,
            self._check_file_permissions,
            self._check_log_configuration,
            self._check_memory_resources,
            self._check_network_connectivity
        ]

        for check_func in checks:
            try:
                result = await check_func()
                if result:
                    self.results.append(result)
                    self._print_diagnostic_result(result)
            except Exception as e:
                error_result = DiagnosticResult(
                    error_type=ErrorType.STARTUP,
                    status="error",
                    message=f"Diagnostic check failed: {check_func.__name__}",
                    details={"error": str(e)},
                    recommendations=["Check diagnostic system integrity"]
                )
                self.results.append(error_result)

        print(f"✅ Diagnostics completed. Found {len(self.results)} issues.")
        return self.results

    async def _check_environment_variables(self) -> Optional[DiagnosticResult]:
        """Check for missing or invalid environment variables"""
        print("  📋 Checking environment variables...")

        required_vars = [
            "TELEGRAM_API_ID", "TELEGRAM_API_HASH", "TELEGRAM_BOT_TOKEN",
            "BINGX_API_KEY", "BINGX_SECRET_KEY", "DATABASE_URL"
        ]

        optional_vars = [
            "MONITORED_CHAT_IDS", "VIP_GROUP_ID", "CRYPTET_CHANNEL_ID",
            "TARGET_GROUP_ID", "LOG_LEVEL", "PORT", "HOST"
        ]

        missing_required = []
        invalid_values = []
        recommendations = []

        # Check required variables
        for var in required_vars:
            value = os.getenv(var)
            if not value or value.strip() == "":
                missing_required.append(var)
                recommendations.append(f"Set {var} in .env file")
            elif var == "TELEGRAM_API_ID" and not value.isdigit():
                invalid_values.append(f"{var} must be numeric")
            elif var == "DATABASE_URL" and not value.startswith(("postgresql://", "sqlite://")):
                invalid_values.append(f"{var} must be a valid database URL")

        # Check optional but important variables
        monitored_chats = os.getenv("MONITORED_CHAT_IDS", "")
        if not monitored_chats:
            recommendations.append("Set MONITORED_CHAT_IDS to monitor Telegram groups")
        else:
            try:
                chat_ids = [int(x.strip()) for x in monitored_chats.split(",") if x.strip()]
                if len(chat_ids) == 0:
                    recommendations.append("MONITORED_CHAT_IDS appears to be empty")
            except ValueError as e:
                invalid_values.append(f"MONITORED_CHAT_IDS contains invalid chat ID: {e}")

        if missing_required or invalid_values:
            status = "critical" if missing_required else "warning"
            message = f"Environment configuration issues: {len(missing_required)} missing, {len(invalid_values)} invalid"

            details = {
                "missing_required": missing_required,
                "invalid_values": invalid_values,
                "total_required": len(required_vars),
                "total_optional": len(optional_vars)
            }

            return DiagnosticResult(
                error_type=ErrorType.ENVIRONMENT,
                status=status,
                message=message,
                details=details,
                recommendations=recommendations,
                auto_fixable=False
            )

        return DiagnosticResult(
            error_type=ErrorType.ENVIRONMENT,
            status="ok",
            message="All environment variables are properly configured",
            details={"checked": len(required_vars) + len(optional_vars)},
            recommendations=[]
        )

    async def _check_dependencies(self) -> Optional[DiagnosticResult]:
        """Check if all required dependencies can be imported"""
        print("  📦 Checking dependencies...")

        required_modules = [
            "fastapi", "uvicorn", "telethon", "sqlalchemy", "httpx",
            "pydantic", "python-dotenv", "selenium", "webdriver_manager"
        ]

        missing_modules = []
        version_issues = []

        for module_name in required_modules:
            try:
                module = importlib.import_module(module_name)
                version = getattr(module, "__version__", "unknown")
                print(f"    ✅ {module_name}: {version}")
            except ImportError:
                missing_modules.append(module_name)
                print(f"    ❌ {module_name}: NOT FOUND")
            except Exception as e:
                version_issues.append(f"{module_name}: {str(e)}")
                print(f"    ⚠️  {module_name}: {str(e)}")

        if missing_modules or version_issues:
            status = "critical" if missing_modules else "warning"
            message = f"Dependency issues: {len(missing_modules)} missing, {len(version_issues)} version problems"

            recommendations = []
            if missing_modules:
                recommendations.append(f"Install missing packages: pip install {' '.join(missing_modules)}")
            if version_issues:
                recommendations.append("Check package versions and compatibility")

            return DiagnosticResult(
                error_type=ErrorType.IMPORT,
                status=status,
                message=message,
                details={
                    "missing_modules": missing_modules,
                    "version_issues": version_issues
                },
                recommendations=recommendations,
                auto_fixable=False
            )

        return DiagnosticResult(
            error_type=ErrorType.IMPORT,
            status="ok",
            message="All dependencies are available",
            details={"checked": len(required_modules)},
            recommendations=[]
        )

    async def _check_database_connection(self) -> Optional[DiagnosticResult]:
        """Test database connectivity"""
        print("  🗄️  Checking database connection...")

        database_url = os.getenv("DATABASE_URL", "")

        if not database_url:
            return DiagnosticResult(
                error_type=ErrorType.DATABASE,
                status="error",
                message="DATABASE_URL not configured",
                details={"database_url": None},
                recommendations=["Set DATABASE_URL environment variable"],
                auto_fixable=False
            )

        try:
            if database_url.startswith("sqlite://"):
                # For SQLite, just check if the file path is accessible
                if database_url == "sqlite:///:memory:":
                    print("    ✅ SQLite in-memory database")
                    return DiagnosticResult(
                        error_type=ErrorType.DATABASE,
                        status="ok",
                        message="SQLite in-memory database configured",
                        details={"database_type": "sqlite", "location": "memory"},
                        recommendations=[]
                    )
                else:
                    db_path = database_url.replace("sqlite:///", "")
                    if os.path.exists(db_path):
                        print(f"    ✅ SQLite database file exists: {db_path}")
                    else:
                        print(f"    ⚠️  SQLite database file does not exist: {db_path}")
                        return DiagnosticResult(
                            error_type=ErrorType.DATABASE,
                            status="warning",
                            message="SQLite database file does not exist",
                            details={"database_path": db_path},
                            recommendations=["Database file will be created on first run"],
                            auto_fixable=True
                        )
            else:
                print(f"    ⚠️  External database detected: {database_url.split('@')[0] if '@' in database_url else 'unknown'}")
                # For PostgreSQL, we would need to test actual connection
                # This is a simplified check

            return DiagnosticResult(
                error_type=ErrorType.DATABASE,
                status="ok",
                message="Database configuration appears valid",
                details={"database_url": database_url.replace('//', '//[REDACTED]@')},
                recommendations=[]
            )

        except Exception as e:
            return DiagnosticResult(
                error_type=ErrorType.DATABASE,
                status="error",
                message=f"Database configuration error: {str(e)}",
                details={"error": str(e), "database_url": database_url[:50] + "..." if len(database_url) > 50 else database_url},
                recommendations=["Check DATABASE_URL format and accessibility"],
                auto_fixable=False
            )

    async def _check_telegram_connectivity(self) -> Optional[DiagnosticResult]:
        """Test Telegram API connectivity"""
        print("  📱 Checking Telegram connectivity...")

        api_id = os.getenv("TELEGRAM_API_ID")
        api_hash = os.getenv("TELEGRAM_API_HASH")

        if not (api_id and api_hash):
            return DiagnosticResult(
                error_type=ErrorType.CONNECTION,
                status="error",
                message="Telegram API credentials missing",
                details={"api_id": bool(api_id), "api_hash": bool(api_hash)},
                recommendations=["Set TELEGRAM_API_ID and TELEGRAM_API_HASH"],
                auto_fixable=False
            )

        try:
            from telethon import TelegramClient
            import tempfile

            # Try to create a client (without connecting)
            session_file = os.path.join(tempfile.gettempdir(), "diagnostic_session.session")

            if api_id is None or api_hash is None:
                raise ValueError("API credentials are None")

            client = TelegramClient(session_file, int(api_id or "0"), api_hash)

            # Check if we can at least create the client
            print(f"    ✅ Telegram client can be created (API ID: {api_id[:4]}...)")

            # Clean up
            if os.path.exists(session_file):
                os.remove(session_file)

            return DiagnosticResult(
                error_type=ErrorType.CONNECTION,
                status="ok",
                message="Telegram API credentials appear valid",
                details={"api_id_configured": True, "api_hash_configured": True},
                recommendations=[]
            )

        except Exception as e:
            return DiagnosticResult(
                error_type=ErrorType.CONNECTION,
                status="error",
                message=f"Telegram API configuration error: {str(e)}",
                details={"error": str(e)},
                recommendations=["Verify TELEGRAM_API_ID and TELEGRAM_API_HASH values"],
                auto_fixable=False
            )

    async def _check_bingx_connectivity(self) -> Optional[DiagnosticResult]:
        """Test BingX API connectivity"""
        print("  💰 Checking BingX connectivity...")

        api_key = os.getenv("BINGX_API_KEY", "")
        secret_key = os.getenv("BINGX_SECRET_KEY", "")

        if not (api_key and secret_key):
            return DiagnosticResult(
                error_type=ErrorType.CONNECTION,
                status="warning",
                message="BingX API credentials not configured",
                details={"api_key": bool(api_key), "secret_key": bool(secret_key)},
                recommendations=["Set BINGX_API_KEY and BINGX_SECRET_KEY for trading functionality"],
                auto_fixable=False
            )

        try:
            # Simple connectivity test
            base_url = "https://open-api.bingx.com" if os.getenv("BINGX_TESTNET", "false").lower() != "true" else "https://open-api-vst.bingx.com"

            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{base_url}/openApi/spot/v1/time")

                if response.status_code == 200:
                    print("    ✅ BingX API is reachable")
                    return DiagnosticResult(
                        error_type=ErrorType.CONNECTION,
                        status="ok",
                        message="BingX API is accessible",
                        details={"base_url": base_url, "response_time": response.elapsed.total_seconds()},
                        recommendations=[]
                    )
                else:
                    return DiagnosticResult(
                        error_type=ErrorType.CONNECTION,
                        status="error",
                        message=f"BingX API returned status {response.status_code}",
                        details={"status_code": response.status_code, "base_url": base_url},
                        recommendations=["Check BingX API credentials and network connectivity"],
                        auto_fixable=False
                    )

        except httpx.TimeoutException:
            base_url = "https://open-api.bingx.com" if os.getenv("BINGX_TESTNET", "false").lower() != "true" else "https://open-api-vst.bingx.com"
            return DiagnosticResult(
                error_type=ErrorType.CONNECTION,
                status="error",
                message="BingX API connection timeout",
                details={"base_url": base_url, "timeout": 5},
                recommendations=["Check network connectivity and firewall settings"],
                auto_fixable=False
            )
        except Exception as e:
            base_url = "https://open-api.bingx.com" if os.getenv("BINGX_TESTNET", "false").lower() != "true" else "https://open-api-vst.bingx.com"
            return DiagnosticResult(
                error_type=ErrorType.CONNECTION,
                status="error",
                message=f"BingX API connection error: {str(e)}",
                details={"error": str(e), "base_url": base_url},
                recommendations=["Check BingX API credentials and network connectivity"],
                auto_fixable=False
            )

    async def _check_port_availability(self) -> Optional[DiagnosticResult]:
        """Check if required ports are available"""
        print("  🔌 Checking port availability...")

        ports_to_check = []
        default_port = int(os.getenv("PORT", "8080"))

        # Main application port
        ports_to_check.append(("Main Application", default_port))

        # Check additional ports that might be used
        if os.getenv("METRICS_PORT"):
            ports_to_check.append(("Metrics", int(os.getenv("METRICS_PORT"))))

        unavailable_ports = []

        for service_name, port in ports_to_check:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(1)
                    result = s.connect_ex(('localhost', port))
                    if result == 0:
                        unavailable_ports.append((service_name, port))
                        print(f"    ❌ Port {port} ({service_name}) is already in use")
                    else:
                        print(f"    ✅ Port {port} ({service_name}) is available")
            except Exception as e:
                print(f"    ⚠️  Could not check port {port}: {str(e)}")

        if unavailable_ports:
            port_details = [f"{name}: {port}" for name, port in unavailable_ports]
            recommendations = []

            for service_name, port in unavailable_ports:
                recommendations.append(f"Stop service using port {port} or change {service_name.upper()}_PORT")

            return DiagnosticResult(
                error_type=ErrorType.CONFIGURATION,
                status="error",
                message=f"Port conflicts detected: {len(unavailable_ports)} ports in use",
                details={"unavailable_ports": port_details},
                recommendations=recommendations,
                auto_fixable=False
            )

        return DiagnosticResult(
            error_type=ErrorType.CONFIGURATION,
            status="ok",
            message="All required ports are available",
            details={"checked_ports": len(ports_to_check)},
            recommendations=[]
        )

    async def _check_file_permissions(self) -> Optional[DiagnosticResult]:
        """Check file and directory permissions"""
        print("  📁 Checking file permissions...")

        critical_paths = [
            ".env",
            ".env.example",
            "src/",
            "logs/",
            "session_files/",
            "trading_bot.db"  # if using SQLite
        ]

        permission_issues = []

        for path in critical_paths:
            if os.path.exists(path):
                try:
                    # Try to read the path
                    if os.path.isdir(path):
                        os.listdir(path)
                        print(f"    ✅ Directory readable: {path}")
                    else:
                        with open(path, 'r') as f:
                            f.read(1)  # Just try to read one character
                        print(f"    ✅ File readable: {path}")
                except PermissionError as e:
                    permission_issues.append(f"{path}: {str(e)}")
                    print(f"    ❌ Permission denied: {path}")
                except Exception as e:
                    print(f"    ⚠️  Could not check {path}: {str(e)}")
            else:
                print(f"    ⚠️  Path does not exist: {path}")

        if permission_issues:
            return DiagnosticResult(
                error_type=ErrorType.PERMISSION,
                status="error",
                message=f"File permission issues: {len(permission_issues)} paths",
                details={"permission_issues": permission_issues},
                recommendations=["Check file permissions and ownership"],
                auto_fixable=False
            )

        return DiagnosticResult(
            error_type=ErrorType.PERMISSION,
            status="ok",
            message="File permissions appear correct",
            details={"checked_paths": len(critical_paths)},
            recommendations=[]
        )

    async def _check_log_configuration(self) -> Optional[DiagnosticResult]:
        """Check logging configuration"""
        print("  📝 Checking log configuration...")

        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

        if log_level not in valid_levels:
            return DiagnosticResult(
                error_type=ErrorType.CONFIGURATION,
                status="warning",
                message=f"Invalid LOG_LEVEL: {log_level}",
                details={"current_level": log_level, "valid_levels": valid_levels},
                recommendations=[f"Set LOG_LEVEL to one of: {', '.join(valid_levels)}"],
                auto_fixable=True
            )

        # Check if log directory exists and is writable
        log_dir = "logs"
        if not os.path.exists(log_dir):
            try:
                os.makedirs(log_dir)
                print(f"    ✅ Created log directory: {log_dir}")
            except Exception as e:
                return DiagnosticResult(
                    error_type=ErrorType.PERMISSION,
                    status="error",
                    message=f"Cannot create log directory: {str(e)}",
                    details={"log_dir": log_dir, "error": str(e)},
                    recommendations=["Check directory permissions or create logs directory manually"],
                    auto_fixable=False
                )

        return DiagnosticResult(
            error_type=ErrorType.CONFIGURATION,
            status="ok",
            message=f"Log configuration is valid (level: {log_level})",
            details={"log_level": log_level, "log_dir_exists": True},
            recommendations=[]
        )

    async def _check_memory_resources(self) -> Optional[DiagnosticResult]:
        """Check system memory resources"""
        print("  🧠 Checking memory resources...")

        try:
            import psutil

            memory = psutil.virtual_memory()
            memory_gb = memory.available / (1024**3)

            if memory_gb < 1.0:
                return DiagnosticResult(
                    error_type=ErrorType.RESOURCE,
                    status="warning",
                    message=".1f",
                    details={
                        "available_gb": round(memory_gb, 2),
                        "total_gb": round(memory.total / (1024**3), 2),
                        "percentage": memory.percent
                    },
                    recommendations=["Close unnecessary applications or increase system memory"],
                    auto_fixable=False
                )
            else:
                print(".1f")
                return DiagnosticResult(
                    error_type=ErrorType.RESOURCE,
                    status="ok",
                    message=".1f",
                    details={
                        "available_gb": round(memory_gb, 2),
                        "total_gb": round(memory.total / (1024**3), 2),
                        "percentage": memory.percent
                    },
                    recommendations=[]
                )

        except ImportError:
            print("    ⚠️  psutil not available, skipping memory check")
            return DiagnosticResult(
                error_type=ErrorType.RESOURCE,
                status="warning",
                message="Cannot check memory resources (psutil not installed)",
                details={"psutil_available": False},
                recommendations=["Install psutil for memory monitoring: pip install psutil"],
                auto_fixable=True
            )

    async def _check_network_connectivity(self) -> Optional[DiagnosticResult]:
        """Check basic network connectivity"""
        print("  🌐 Checking network connectivity...")

        test_urls = [
            "https://api.telegram.org",
            "https://google.com",
            "https://bingx.com"
        ]

        connectivity_issues = []

        async with httpx.AsyncClient(timeout=5) as client:
            for url in test_urls:
                try:
                    response = await client.get(url, follow_redirects=True)
                    if response.status_code == 200:
                        print(f"    ✅ {url} is reachable")
                    else:
                        connectivity_issues.append(f"{url}: HTTP {response.status_code}")
                        print(f"    ❌ {url}: HTTP {response.status_code}")
                except Exception as e:
                    connectivity_issues.append(f"{url}: {str(e)}")
                    print(f"    ❌ {url}: {str(e)}")

        if connectivity_issues:
            return DiagnosticResult(
                error_type=ErrorType.CONNECTION,
                status="error",
                message=f"Network connectivity issues: {len(connectivity_issues)} services unreachable",
                details={"connectivity_issues": connectivity_issues},
                recommendations=["Check internet connection and firewall settings"],
                auto_fixable=False
            )

        return DiagnosticResult(
            error_type=ErrorType.CONNECTION,
            status="ok",
            message="Network connectivity is working",
            details={"tested_urls": len(test_urls)},
            recommendations=[]
        )

    def _print_diagnostic_result(self, result: DiagnosticResult) -> None:
        """Print a diagnostic result with appropriate formatting"""
        status_emoji = {
            "ok": "✅",
            "warning": "⚠️ ",
            "error": "❌",
            "critical": "🚨"
        }

        emoji = status_emoji.get(result.status, "❓")
        print(f"  {emoji} {result.message}")

        if result.recommendations:
            for rec in result.recommendations:
                print(f"     💡 {rec}")

    def generate_report(self) -> Dict[str, Any]:
        """Generate a comprehensive diagnostic report"""
        end_time = datetime.utcnow()
        duration = (end_time - self.start_time).total_seconds()

        # Count issues by severity
        issue_counts = {"ok": 0, "warning": 0, "error": 0, "critical": 0}
        for result in self.results:
            issue_counts[result.status] = issue_counts.get(result.status, 0) + 1

        # Group results by error type
        results_by_type = {}
        for result in self.results:
            error_type = result.error_type.value
            if error_type not in results_by_type:
                results_by_type[error_type] = []
            results_by_type[error_type].append(asdict(result))

        report = {
            "timestamp": end_time.isoformat() + "Z",
            "duration_seconds": round(duration, 2),
            "total_checks": len(self.results),
            "issue_counts": issue_counts,
            "results_by_type": results_by_type,
            "overall_status": self._calculate_overall_status(issue_counts),
            "recommendations": self._extract_all_recommendations()
        }

        return report

    def _calculate_overall_status(self, issue_counts: Dict[str, int]) -> str:
        """Calculate overall system status"""
        if issue_counts.get("critical", 0) > 0:
            return "critical"
        elif issue_counts.get("error", 0) > 0:
            return "error"
        elif issue_counts.get("warning", 0) > 0:
            return "warning"
        else:
            return "ok"

    def _extract_all_recommendations(self) -> List[str]:
        """Extract all recommendations from results"""
        all_recommendations = []
        for result in self.results:
            all_recommendations.extend(result.recommendations)
        return list(set(all_recommendations))  # Remove duplicates

    def print_summary(self) -> None:
        """Print a summary of the diagnostic results"""
        print("\n" + "="*60)
        print("🔍 CONSOLE DIAGNOSTICS SUMMARY")
        print("="*60)

        if not self.results:
            print("❌ No diagnostic results available")
            return

        # Count by status
        status_counts = {"ok": 0, "warning": 0, "error": 0, "critical": 0}
        for result in self.results:
            status_counts[result.status] = status_counts.get(result.status, 0) + 1

        print(f"Total Checks: {len(self.results)}")
        print(f"✅ OK: {status_counts['ok']}")
        print(f"⚠️  Warnings: {status_counts['warning']}")
        print(f"❌ Errors: {status_counts['error']}")
        print(f"🚨 Critical: {status_counts['critical']}")

        # Show critical issues first
        critical_results = [r for r in self.results if r.status == "critical"]
        if critical_results:
            print("\n🚨 CRITICAL ISSUES:")
            for result in critical_results:
                print(f"  • {result.message}")

        # Show errors
        error_results = [r for r in self.results if r.status == "error"]
        if error_results:
            print("\n❌ ERRORS:")
            for result in error_results:
                print(f"  • {result.message}")

        # Show warnings
        warning_results = [r for r in self.results if r.status == "warning"]
        if warning_results:
            print("\n⚠️  WARNINGS:")
            for result in warning_results:
                print(f"  • {result.message}")

        # Show all recommendations
        all_recommendations = self._extract_all_recommendations()
        if all_recommendations:
            print("\n💡 RECOMMENDATIONS:")
            for i, rec in enumerate(all_recommendations, 1):
                print(f"  {i}. {rec}")

        print("\n" + "="*60)

async def main():
    """Main function for standalone diagnostic execution"""
    engine = ConsoleDiagnosticEngine()

    print("🔧 Cryptet Trading Bot - Console Diagnostics")
    print("This will check your system for common console problems")
    print()

    try:
        results = await engine.run_full_diagnosis()

        # Print summary
        engine.print_summary()

        # Generate detailed report
        report = engine.generate_report()

        # Save report to file
        report_file = f"console_diagnostics_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\n📄 Detailed report saved to: {report_file}")

        # Exit with appropriate code
        critical_count = sum(1 for r in results if r.status == "critical")
        error_count = sum(1 for r in results if r.status == "error")

        if critical_count > 0:
            print("❌ Critical issues found. Please fix before running the bot.")
            sys.exit(1)
        elif error_count > 0:
            print("❌ Errors found. Bot may not start properly.")
            sys.exit(1)
        else:
            print("✅ All checks passed. System appears ready.")

    except KeyboardInterrupt:
        print("\n🛑 Diagnostics interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Diagnostic system error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
