"""
Run all tests with one command.
Run with: python tests/run_all_tests.py
"""

import os
import sys

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'your_project.settings')

import django
django.setup()

def run_health_check():
    """Run system health check"""
    print("\n" + "="*60)
    print(" SYSTEM HEALTH CHECK")
    print("="*60)
    
    from django.test.runner import DiscoverRunner
    runner = DiscoverRunner(verbosity=2)
    
    # Run health tests
    print("\nRunning health checks...")
    result = runner.run_tests(['tests.test_system_health'])
    
    return result

def run_functionality_tests():
    """Run functionality tests"""
    print("\n" + "="*60)
    print(" CORE FUNCTIONALITY TESTS")
    print("="*60)
    
    from django.test.runner import DiscoverRunner
    runner = DiscoverRunner(verbosity=2)
    
    print("\nRunning functionality tests...")
    result = runner.run_tests(['tests.test_functionality'])
    
    return result

def run_workflow_tests():
    """Run workflow tests"""
    print("\n" + "="*60)
    print(" WORKFLOW TESTS")
    print("="*60)
    
    from django.test.runner import DiscoverRunner
    runner = DiscoverRunner(verbosity=2)
    
    print("\nRunning workflow tests...")
    result = runner.run_tests(['tests.test_workflows'])
    
    return result

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print(" COMPREHENSIVE FINANCIAL SYSTEM TEST SUITE")
    print("="*60)
    
    # Run tests in sequence
    health_result = run_health_check()
    
    if health_result:
        print("\n Health checks passed, proceeding to functionality tests...")
        func_result = run_functionality_tests()
        
        if func_result:
            print("\n Functionality tests passed, proceeding to workflow tests...")
            workflow_result = run_workflow_tests()
            
            if workflow_result:
                print("\n" + "="*60)
                print(" ALL TESTS PASSED!")
                print("="*60)
                print("\nYour financial system is READY for development!")
            else:
                print("\n  Workflow tests failed, but core system is functional")
        else:
            print("\n Functionality tests failed - check core models")
    else:
        print("\n Health checks failed - system not ready")
    
    print("\n" + "="*60)
    print(" TEST EXECUTION COMPLETE")
    print("="*60)

if __name__ == "__main__":
    main()
