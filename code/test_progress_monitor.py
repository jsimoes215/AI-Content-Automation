#!/usr/bin/env python3
"""
Simple test for the Progress Monitoring System

This test verifies that the progress monitor can be imported and basic
functionality works without external dependencies.
"""

import sys
import os
import time
from datetime import datetime

# Add the code directory to the path so we can import the module
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

def test_imports():
    """Test that all modules can be imported."""
    print("🧪 Testing imports...")
    
    try:
        from progress_monitor import (
            ProgressMonitor, JobState, VideoState, EventType,
            JobProgress, VideoProgress, WebSocketMessage,
            ProgressCalculator, SupabaseRealtimeClient,
            WebSocketBroadcaster
        )
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False


def test_enums():
    """Test enum definitions."""
    print("\n🧪 Testing enums...")
    
    from progress_monitor import JobState, VideoState, EventType
    
    # Test JobState
    assert hasattr(JobState, 'PENDING')
    assert hasattr(JobState, 'RUNNING')
    assert hasattr(JobState, 'COMPLETED')
    assert JobState.PENDING.value == "pending"
    
    # Test VideoState
    assert hasattr(VideoState, 'PENDING')
    assert hasattr(VideoState, 'PROCESSING')
    assert hasattr(VideoState, 'COMPLETED')
    assert VideoState.PROCESSING.value == "processing"
    
    # Test EventType
    assert hasattr(EventType, 'JOB_STATE_CHANGED')
    assert hasattr(EventType, 'JOB_PROGRESS')
    assert hasattr(EventType, 'VIDEO_COMPLETED')
    assert EventType.JOB_PROGRESS.value == "job.progress"
    
    print("✅ All enums working correctly")
    return True


def test_progress_calculator():
    """Test progress calculation logic."""
    print("\n🧪 Testing progress calculator...")
    
    from progress_monitor import ProgressCalculator, JobState
    
    calculator = ProgressCalculator()
    
    # Test basic progress calculation
    job_data = {
        'id': 'test_job',
        'items_total': 100,
        'items_completed': 25,
        'items_failed': 2,
        'items_skipped': 1,
        'items_canceled': 0,
        'created_at': datetime.utcnow(),
        'state': JobState.RUNNING.value
    }
    
    progress = calculator.calculate_progress(job_data)
    
    # Verify calculations
    assert progress.percent_complete == 26.0  # (25 + 1) / 100 * 100
    assert progress.items_total == 100
    assert progress.items_completed == 25
    assert progress.items_failed == 2
    assert progress.items_skipped == 1
    assert progress.items_canceled == 0
    assert progress.items_pending == 72  # 100 - 25 - 2 - 1 - 0
    
    # Test with completed items
    calculator.record_item_completion('test_job', 'item1', True)
    calculator.record_item_completion('test_job', 'item2', True)
    
    time.sleep(0.1)  # Small delay
    
    progress2 = calculator.calculate_progress(job_data)
    
    # Should have processing history now
    assert progress2.time_processing_ms > 0
    assert progress2.average_duration_ms_per_item is not None
    
    print("✅ Progress calculator working correctly")
    return True


def test_dataclasses():
    """Test data class definitions."""
    print("\n🧪 Testing data classes...")
    
    from progress_monitor import (
        JobProgress, VideoProgress, WebSocketMessage,
        EventType, JobState, VideoState
    )
    
    # Test JobProgress
    job_progress = JobProgress(
        percent_complete=50.0,
        items_total=100,
        items_completed=50,
        items_failed=0,
        items_skipped=0,
        items_canceled=0,
        items_pending=50,
        time_to_start_ms=1000,
        time_processing_ms=5000,
        average_duration_ms_per_item=100.0,
        eta_ms=5000,
        rate_limited=False,
        processing_deadline_ms=3600000,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    assert job_progress.percent_complete == 50.0
    assert job_progress.items_total == 100
    
    # Test VideoProgress
    video_progress = VideoProgress(
        id='vid_001',
        job_id='job_001',
        state=VideoState.COMPLETED,
        percent_complete=100.0,
        row_index=1,
        title='Test Video',
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        errors=[]
    )
    
    assert video_progress.id == 'vid_001'
    assert video_progress.state == VideoState.COMPLETED
    assert video_progress.percent_complete == 100.0
    
    # Test WebSocketMessage
    message = WebSocketMessage(
        type=EventType.JOB_PROGRESS,
        ts=datetime.utcnow().isoformat(),
        correlation_id='test-corr-id',
        data={'test': 'data'}
    )
    
    assert message.type == EventType.JOB_PROGRESS
    assert message.data['test'] == 'data'
    
    print("✅ All data classes working correctly")
    return True


def test_basic_monitor_creation():
    """Test basic monitor creation without starting services."""
    print("\n🧪 Testing monitor creation...")
    
    try:
        from progress_monitor import ProgressMonitor, JobState
        
        # Create monitor with dummy credentials (won't connect)
        monitor = ProgressMonitor(
            supabase_url='http://localhost:54321',
            supabase_key='test_key',
            ws_host='127.0.0.1',
            ws_port=9999
        )
        
        # Test that attributes exist
        assert hasattr(monitor, 'progress_calculator')
        assert hasattr(monitor, 'active_jobs')
        assert hasattr(monitor, 'state_change_handlers')
        assert hasattr(monitor, 'progress_handlers')
        
        # Test handler registration
        def test_handler(job_id, prior_state, new_state, reason):
            pass
        
        monitor.add_state_change_handler(test_handler)
        assert len(monitor.state_change_handlers) == 1
        
        def progress_handler(job_id, progress):
            pass
        
        monitor.add_progress_handler(progress_handler)
        assert len(monitor.progress_handlers) == 1
        
        # Test job registration (without starting services)
        job_data = {
            'id': 'test_job_001',
            'state': JobState.PENDING.value,
            'items_total': 10,
            'items_completed': 0,
            'items_failed': 0,
            'items_skipped': 0,
            'items_canceled': 0,
            'created_at': datetime.utcnow().isoformat(),
            'rate_limited': False
        }
        
        # Register job (this should work without Supabase connection)
        monitor.register_job('test_job_001', job_data)
        
        # Verify job is registered
        assert 'test_job_001' in monitor.active_jobs
        assert monitor.active_jobs['test_job_001']['state'] == JobState.PENDING
        
        # Test job status retrieval
        status = monitor.get_job_status('test_job_001')
        assert status is not None
        assert status['id'] == 'test_job_001'
        
        # Test job state update
        monitor.update_job_state('test_job_001', JobState.RUNNING, 'test_reason')
        assert monitor.active_jobs['test_job_001']['state'] == JobState.RUNNING
        
        # Test progress update
        job_data['items_completed'] = 5
        job_data['state'] = JobState.RUNNING.value
        monitor.update_job_progress('test_job_001', job_data)
        
        # Test unregistration
        monitor.unregister_job('test_job_001')
        assert 'test_job_001' not in monitor.active_jobs
        
        print("✅ Monitor creation and basic operations working")
        return True
        
    except Exception as e:
        print(f"❌ Monitor test failed: {e}")
        return False


def test_job_lifecycle_simulation():
    """Test a complete job lifecycle simulation."""
    print("\n🧪 Testing job lifecycle simulation...")
    
    from progress_monitor import ProgressMonitor, JobState, VideoState
    
    monitor = ProgressMonitor(
        supabase_url='http://localhost:54321',
        supabase_key='test_key'
    )
    
    # Job creation
    job_id = 'lifecycle_test_job'
    job_data = {
        'id': job_id,
        'state': JobState.PENDING.value,
        'items_total': 5,
        'items_completed': 0,
        'items_failed': 0,
        'items_skipped': 0,
        'items_canceled': 0,
        'created_at': datetime.utcnow().isoformat(),
        'rate_limited': False
    }
    
    # Simulate lifecycle
    states_seen = []
    
    def track_states(job_id, prior_state, new_state, reason):
        states_seen.append((prior_state, new_state, reason))
    
    monitor.add_state_change_handler(track_states)
    
    # Start monitoring (without WebSocket server)
    monitor._running = True
    
    try:
        # Create job
        monitor.register_job(job_id, job_data)
        assert JobState.PENDING in [s[0] for s in states_seen]
        
        # Start job
        monitor.update_job_state(job_id, JobState.RUNNING, "worker_assigned")
        assert (JobState.PENDING, JobState.RUNNING, "worker_assigned") in states_seen
        
        # Simulate progress
        for i in range(1, 6):
            job_data['items_completed'] = i
            job_data['state'] = JobState.RUNNING.value
            monitor.update_job_progress(job_id, job_data)
            
            # Simulate video completion
            video_data = {
                'id': f'vid_{i:03d}',
                'state': VideoState.COMPLETED.value,
                'percent_complete': 100.0,
                'row_index': i,
                'title': f'Video {i}',
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            monitor.update_video_progress(job_id, video_data)
        
        # Complete job
        monitor.update_job_state(job_id, JobState.COMPLETED, "all_items_processed")
        assert (JobState.RUNNING, JobState.COMPLETED, "all_items_processed") in states_seen
        
        # Verify final state
        final_status = monitor.get_job_status(job_id)
        assert final_status['state'] == JobState.COMPLETED
        
        # Check progress calculation
        final_progress = monitor.progress_calculator.calculate_progress(job_data)
        assert final_progress.percent_complete == 100.0
        assert final_progress.items_completed == 5
        assert final_progress.items_pending == 0
        
        print("✅ Job lifecycle simulation completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Lifecycle test failed: {e}")
        return False
    finally:
        monitor._running = False


def run_all_tests():
    """Run all tests and report results."""
    print("🚀 Running Progress Monitor Tests")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_enums,
        test_progress_calculator,
        test_dataclasses,
        test_basic_monitor_creation,
        test_job_lifecycle_simulation
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test.__name__} crashed: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! The progress monitor is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)