#!/usr/bin/env python3
"""
AI Influencer Management POC - System Launcher
Sets up and runs the complete AI influencer management system

Author: MiniMax Agent
Date: 2025-11-07
"""

import os
import sys
import subprocess
import time
import json
import sqlite3
from pathlib import Path
import signal
import threading
from typing import Dict, List, Optional

# ANSI color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

class AIInfluencerPOCLauncher:
    def __init__(self):
        self.project_root = Path("/workspace/ai_influencer_poc")
        self.backend_dir = self.project_root / "api"
        self.frontend_dir = self.project_root / "frontend"
        self.database_dir = self.project_root / "database"
        
        self.processes: Dict[str, subprocess.Popen] = {}
        self.setup_complete = False
        
    def print_banner(self):
        """Print system banner"""
        banner = f"""
{Colors.CYAN}{Colors.BOLD}
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║    ██████╗ ███████╗███████╗████████╗██╗   ██╗██████╗  ██████╗ ███████╗      ║
║   ██╔══██╗██╔════╝██╔════╝╚══██╔══╝██║   ██║██╔══██╗██╔═══██╗██╔════╝      ║
║   ██████╔╝█████╗  ███████╗   ██║   ██║   ██║██████╔╝██║   ██║███████╗      ║
║   ██╔══██╗██╔══╝  ╚════██║   ██║   ██║   ██║██╔═══╝ ██║   ██║╚════██║      ║
║   ██║  ██║███████╗███████║   ██║   ╚██████╔╝██║     ╚██████╔╝███████║      ║
║   ╚═╝  ╚═╝╚══════╝╚══════╝   ╚═╝    ╚═════╝ ╚═╝      ╚═════╝ ╚══════╝      ║
║                                                                              ║
║                    AI Influencer Management System                          ║
║                                                                              ║
║                        Proof of Concept (POC)                               ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
{Colors.END}

{Colors.WHITE}Author: MiniMax Agent{Colors.END}
{Colors.WHITE}Date: 2025-11-07{Colors.END}
{Colors.WHITE}Version: 1.0.0 - POC{Colors.END}
        """
        print(banner)
    
    def print_step(self, step: str, description: str):
        """Print formatted step"""
        print(f"\n{Colors.BLUE}{Colors.BOLD}▶ {step}{Colors.END} {description}")
    
    def print_success(self, message: str):
        """Print success message"""
        print(f"  {Colors.GREEN}✓ {message}{Colors.END}")
    
    def print_error(self, message: str):
        """Print error message"""
        print(f"  {Colors.RED}✗ {message}{Colors.END}")
    
    def print_warning(self, message: str):
        """Print warning message"""
        print(f"  {Colors.YELLOW}⚠ {message}{Colors.END}")
    
    def print_info(self, message: str):
        """Print info message"""
        print(f"  {Colors.CYAN}ℹ {message}{Colors.END}")
    
    def check_system_requirements(self):
        """Check if system requirements are met"""
        self.print_step("STEP 1", "Checking System Requirements")
        
        requirements = {
            "Python 3.8+": False,
            "Node.js 16+": False,
            "npm": False,
            "Git": False
        }
        
        # Check Python
        try:
            result = subprocess.run([sys.executable, "--version"], capture_output=True, text=True)
            if "Python 3.8" in result.stdout or "Python 3.9" in result.stdout or "Python 3.10" in result.stdout or "Python 3.11" in result.stdout or "Python 3.12" in result.stdout:
                requirements["Python 3.8+"] = True
                self.print_success(f"Python: {result.stdout.strip()}")
            else:
                self.print_error(f"Python version too old: {result.stdout.strip()}")
        except Exception as e:
            self.print_error(f"Python check failed: {e}")
        
        # Check Node.js
        try:
            result = subprocess.run(["node", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                requirements["Node.js 16+"] = True
                self.print_success(f"Node.js: {result.stdout.strip()}")
            else:
                self.print_error("Node.js not found")
        except Exception:
            self.print_error("Node.js not found")
        
        # Check npm
        try:
            result = subprocess.run(["npm", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                requirements["npm"] = True
                self.print_success(f"npm: {result.stdout.strip()}")
            else:
                self.print_error("npm not found")
        except Exception:
            self.print_error("npm not found")
        
        # Check Git
        try:
            result = subprocess.run(["git", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                requirements["Git"] = True
                self.print_success(f"Git: {result.stdout.strip()}")
            else:
                self.print_error("Git not found")
        except Exception:
            self.print_error("Git not found")
        
        all_met = all(requirements.values())
        if all_met:
            self.print_success("All system requirements met")
        else:
            self.print_error("Some system requirements are missing")
            missing = [req for req, met in requirements.items() if not met]
            print(f"Missing: {', '.join(missing)}")
            return False
        
        return True
    
    def setup_project_structure(self):
        """Create project directory structure"""
        self.print_step("STEP 2", "Setting Up Project Structure")
        
        directories = [
            self.project_root,
            self.project_root / "api",
            self.project_root / "frontend",
            self.project_root / "frontend" / "src",
            self.project_root / "frontend" / "public",
            self.project_root / "frontend" / "src" / "components",
            self.project_root / "database",
            self.project_root / "database" / "migrations",
            self.project_root / "scripts",
            self.project_root / "logs"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            self.print_info(f"Created directory: {directory.relative_to(self.project_root)}")
        
        self.print_success("Project structure created")
    
    def setup_backend(self):
        """Setup backend dependencies and database"""
        self.print_step("STEP 3", "Setting Up Backend")
        
        # Install Python dependencies
        self.print_info("Installing Python dependencies...")
        requirements_file = self.project_root / "requirements.txt"
        if requirements_file.exists():
            try:
                subprocess.run([
                    sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
                ], check=True, capture_output=True)
                self.print_success("Python dependencies installed")
            except subprocess.CalledProcessError as e:
                self.print_error(f"Failed to install Python dependencies: {e}")
                return False
        else:
            self.print_warning("requirements.txt not found, installing basic dependencies...")
            basic_deps = ["fastapi", "uvicorn[standard]", "python-multipart", "pydantic"]
            try:
                subprocess.run([
                    sys.executable, "-m", "pip", "install"
                ] + basic_deps, check=True, capture_output=True)
                self.print_success("Basic Python dependencies installed")
            except subprocess.CalledProcessError as e:
                self.print_error(f"Failed to install basic dependencies: {e}")
                return False
        
        # Setup database
        self.print_info("Setting up database...")
        try:
            # Run the database migration script
            migration_script = self.project_root / "database" / "migrations" / "001_create_influencers_schema.py"
            if migration_script.exists():
                subprocess.run([sys.executable, str(migration_script)], check=True)
                self.print_success("Database schema created and populated")
            else:
                self.print_error("Database migration script not found")
                return False
        except subprocess.CalledProcessError as e:
            self.print_error(f"Database setup failed: {e}")
            return False
        
        return True
    
    def setup_frontend(self):
        """Setup frontend dependencies"""
        self.print_step("STEP 4", "Setting Up Frontend")
        
        # Install Node.js dependencies
        self.print_info("Installing Node.js dependencies...")
        try:
            # First try npm install
            result = subprocess.run([
                "npm", "install", "--silent"
            ], cwd=self.frontend_dir, capture_output=True, text=True)
            
            if result.returncode == 0:
                self.print_success("Node.js dependencies installed")
            else:
                self.print_warning("npm install had issues, trying with legacy peer deps...")
                # Try with legacy peer deps
                result = subprocess.run([
                    "npm", "install", "--legacy-peer-deps", "--silent"
                ], cwd=self.frontend_dir, capture_output=True, text=True)
                
                if result.returncode == 0:
                    self.print_success("Node.js dependencies installed (legacy peer deps)")
                else:
                    self.print_error(f"Failed to install Node.js dependencies: {result.stderr}")
                    return False
                    
        except Exception as e:
            self.print_error(f"Failed to install Node.js dependencies: {e}")
            return False
        
        return True
    
    def start_backend(self):
        """Start the FastAPI backend server"""
        self.print_step("STEP 5", "Starting Backend Server")
        
        try:
            # Start the FastAPI server
            env = os.environ.copy()
            env['PYTHONPATH'] = str(self.project_root)
            
            self.print_info("Starting FastAPI server on http://localhost:8000")
            print(f"  API Documentation: {Colors.CYAN}http://localhost:8000/docs{Colors.END}")
            print(f"  API ReDoc: {Colors.CYAN}http://localhost:8000/redoc{Colors.END}")
            
            process = subprocess.Popen([
                sys.executable, "-m", "uvicorn", 
                "api.main:app",
                "--host", "0.0.0.0",
                "--port", "8000",
                "--reload"
            ], cwd=self.project_root, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            self.processes["backend"] = process
            time.sleep(3)  # Give server time to start
            
            if process.poll() is None:
                self.print_success("Backend server started successfully")
                return True
            else:
                self.print_error("Backend server failed to start")
                return False
                
        except Exception as e:
            self.print_error(f"Failed to start backend: {e}")
            return False
    
    def start_frontend(self):
        """Start the React frontend development server"""
        self.print_step("STEP 6", "Starting Frontend Server")
        
        try:
            self.print_info("Starting React development server on http://localhost:3000")
            print(f"  Application: {Colors.CYAN}http://localhost:3000{Colors.END}")
            
            process = subprocess.Popen([
                "npm", "start"
            ], cwd=self.frontend_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            self.processes["frontend"] = process
            time.sleep(5)  # Give server time to start
            
            if process.poll() is None:
                self.print_success("Frontend server started successfully")
                return True
            else:
                self.print_error("Frontend server failed to start")
                return False
                
        except Exception as e:
            self.print_error(f"Failed to start frontend: {e}")
            return False
    
    def print_system_info(self):
        """Print system information and URLs"""
        info = f"""
{Colors.GREEN}{Colors.BOLD}╔══════════════════════════════════════════════════════════════════════════════╗{Colors.END}
{Colors.GREEN}{Colors.BOLD}║{Colors.END}                                                                              {Colors.GREEN}{Colors.BOLD}║{Colors.END}
{Colors.GREEN}{Colors.BOLD}║{Colors.END}  {Colors.WHITE}{Colors.BOLD}🎉 AI Influencer Management System is now running!{Colors.END}                           {Colors.GREEN}{Colors.BOLD}║{Colors.END}
{Colors.GREEN}{Colors.BOLD}║{Colors.END}                                                                              {Colors.GREEN}{Colors.BOLD}║{Colors.END}
{Colors.GREEN}{Colors.BOLD}║{Colors.END}  {Colors.CYAN}📱 Application:{Colors.END}     http://localhost:3000                              {Colors.GREEN}{Colors.BOLD}║{Colors.END}
{Colors.GREEN}{Colors.BOLD}║{Colors.END}  {Colors.CYAN}🔧 API Documentation:{Colors.END} http://localhost:8000/docs                    {Colors.GREEN}{Colors.BOLD}║{Colors.END}
{Colors.GREEN}{Colors.BOLD}║{Colors.END}  {Colors.CYAN}📊 API ReDoc:{Colors.END}        http://localhost:8000/redoc                     {Colors.GREEN}{Colors.BOLD}║{Colors.END}
{Colors.GREEN}{Colors.BOLD}║{Colors.END}  {Colors.CYAN}💾 Health Check:{Colors.END}     http://localhost:8000/health                   {Colors.GREEN}{Colors.BOLD}║{Colors.END}
{Colors.GREEN}{Colors.BOLD}║{Colors.END}                                                                              {Colors.GREEN}{Colors.BOLD}║{Colors.END}
{Colors.GREEN}{Colors.BOLD}║{Colors.END}  {Colors.WHITE}✨ Features Available:{Colors.END}                                         {Colors.GREEN}{Colors.BOLD}║{Colors.END}
{Colors.GREEN}{Colors.BOLD}║{Colors.END}                                                                              {Colors.GREEN}{Colors.BOLD}║{Colors.END}
{Colors.GREEN}{Colors.BOLD}║{Colors.END}  {Colors.PURPLE}• Manage AI Influencers{Colors.END}                                        {Colors.GREEN}{Colors.BOLD}║{Colors.END}
{Colors.GREEN}{Colors.BOLD}║{Colors.END}  {Colors.PURPLE}• Browse Available Niches{Colors.END}                                      {Colors.GREEN}{Colors.BOLD}║{Colors.END}
{Colors.GREEN}{Colors.BOLD}║{Colors.END}  {Colors.PURPLE}• View System Analytics{Colors.END}                                       {Colors.GREEN}{Colors.BOLD}║{Colors.END}
{Colors.GREEN}{Colors.BOLD}║{Colors.END}  {Colors.PURPLE}• REST API for Integration{Colors.END}                                     {Colors.GREEN}{Colors.BOLD}║{Colors.END}
{Colors.GREEN}{Colors.BOLD}║{Colors.END}                                                                              {Colors.GREEN}{Colors.BOLD}║{Colors.END}
{Colors.GREEN}{Colors.BOLD}║{Colors.END}  {Colors.YELLOW}⚠ To stop the system, press Ctrl+C{Colors.END}                               {Colors.GREEN}{Colors.BOLD}║{Colors.END}
{Colors.GREEN}{Colors.BOLD}║{Colors.END}                                                                              {Colors.GREEN}{Colors.BOLD}║{Colors.END}
{Colors.GREEN}{Colors.BOLD}╚══════════════════════════════════════════════════════════════════════════════╝{Colors.END}
        """
        print(info)
    
    def monitor_processes(self):
        """Monitor running processes and show status"""
        while True:
            time.sleep(10)
            
            # Check if processes are still running
            for name, process in self.processes.items():
                if process.poll() is not None:
                    self.print_error(f"{name.title()} server has stopped unexpectedly")
                    return False
            
            # Show periodic status
            print(f"\n{Colors.CYAN}System Status:{Colors.END} All services running normally")
            time.sleep(30)
    
    def shutdown(self):
        """Shutdown all processes"""
        print(f"\n{Colors.YELLOW}Shutting down system...{Colors.END}")
        
        for name, process in self.processes.items():
            if process.poll() is None:
                self.print_info(f"Stopping {name} server...")
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.print_warning(f"Force killing {name} server...")
                    process.kill()
        
        self.print_success("System shutdown complete")
        sys.exit(0)
    
    def handle_keyboard_interrupt(self, signum, frame):
        """Handle Ctrl+C"""
        print(f"\n{Colors.YELLOW}Received interrupt signal{Colors.END}")
        self.shutdown()
    
    def run(self):
        """Main execution method"""
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.handle_keyboard_interrupt)
        signal.signal(signal.SIGTERM, self.handle_keyboard_interrupt)
        
        # Print banner
        self.print_banner()
        
        # Run setup steps
        try:
            if not self.check_system_requirements():
                self.print_error("System requirements not met. Please install missing dependencies.")
                return False
            
            self.setup_project_structure()
            
            if not self.setup_backend():
                self.print_error("Backend setup failed")
                return False
            
            if not self.setup_frontend():
                self.print_error("Frontend setup failed")
                return False
            
            # Start services
            if not self.start_backend():
                return False
            
            if not self.start_frontend():
                return False
            
            # Show system info and start monitoring
            self.print_system_info()
            self.print_success("POC System is now running!")
            
            # Start monitoring
            try:
                self.monitor_processes()
            except KeyboardInterrupt:
                self.shutdown()
                
        except Exception as e:
            self.print_error(f"Setup failed: {e}")
            self.shutdown()
            return False
        
        return True

def main():
    """Main function"""
    launcher = AIInfluencerPOCLauncher()
    
    try:
        success = launcher.run()
        if success:
            print(f"\n{Colors.GREEN}AI Influencer POC completed successfully!{Colors.END}")
            sys.exit(0)
        else:
            print(f"\n{Colors.RED}AI Influencer POC failed to start properly{Colors.END}")
            sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Fatal error: {e}{Colors.END}")
        sys.exit(1)

if __name__ == "__main__":
    main()