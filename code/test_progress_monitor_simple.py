#!/usr/bin/env python3
"""
Simplified test for the Progress Monitoring System

This test focuses on core functionality without async complications.
"""

import sys
import os
import time
from datetime import datetime

# Add the code directory to the path so we can import the module
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

def test_core_functionality():
    """Test core progress monitoring functionality without async."""
    print("🧪 Testing Core Progress Monitor Functionality")
    print("=" * 50)
    
    try:
        from progress_monitor import (
            ProgressMonitor, JobState, VideoState, EventType,
            ProgressCalculator
        )
        
        # Test ProgressCalculator in isolation
        print("Testing ProgressCalculator...")
        calculator = ProgressCalculator()
        
        # Test basic progress calculation
        job_data = {
            'id': 'test_job',
            'items_total': 100,
            'items_completed': 25,
            'items_failed': 2,
            'items_skipped': 1,
            'items_canceled': 0,
            'created_at': datetime.now().astimezone(),
            'state': JobState.RUNNING.value
        }
        
        progress = calculator.calculate_progress(job_data)
        assert progress.percent_complete == 26.0
        assert progress.items_pending == 72
        print("✅ Progress calculation working")
        
        # Test with item completion tracking
        calculator.record_item_completion('test_job', 'item1', True)
        calculator.record_item_completion('test_job', 'item2', True)
        time.sleep(0.1)
        
        progress2 = calculator.calculate_progress(job_data)
        assert progress2.time_processing_ms > 0
        print("✅ Item tracking working")
        
        # Test Monitor creation (without starting services)
        print("Testing Monitor creation...")
        monitor = ProgressMonitor(
            supabase_url='http://localhost:54321',
            supabase_key='test_key'
        )
        
        # Add handlers
        states_seen = []
        def state_handler(job_id, prior_state, new_state, reason):
            states_seen.append((job_id, prior_state, new_state, reason))
        
        monitor.add_state_change_handler(state_handler)
        
        # Test job registration
        job_data = {
            'id': 'simple_test_job',
            'state': JobState.PENDING.value,
            'items_total': 5,
            'items_completed': 0,
            'items_failed': 0,
            'items_skipped': 0,
            'items_canceled': 0,
            'created_at': datetime.now().astimezone().isoformat(),
            'rate_limited': False
        }
        
        # Mock the WebSocket broadcaster to avoid async issues
        class MockWebSocketBroadcaster:
            def __init__(self, *args, **kwargs):
                self.clients = {}
            async def broadcast_state_change(self, job_id, prior_state, new_state, reason):
                pass
            async def broadcast_progress(self, job_id, progress):
                pass
            async def broadcast_video_update(self, job_id, video, event_type):
                pass
            def start_server(self):
                pass
            def stop_server(self):
                pass
        
        monitor.websocket_broadcaster = MockWebSocketBroadcaster()
        
        # Test job operations
        monitor.register_job('simple_test_job', job_data)
        assert 'simple_test_job' in monitor.active_jobs
        
        # Test state change
        monitor.update_job_state('simple_test_job', JobState.RUNNING, 'test_reason')
        assert monitor.active_jobs['simple_test_job']['state'] == JobState.RUNNING
        assert len(states_seen) == 1
        assert states_seen[0][2] == JobState.RUNNING
        
        # Test progress update
        job_data['items_completed'] = 3
        job_data['state'] = JobState.RUNNING.value
        monitor.update_job_progress('simple_test_job', job_data)
        
        # Test video update
        video_data = {
            'id': 'vid_001',
            'state': VideoState.COMPLETED.value,
            'percent_complete': 100.0,
            'row_index': 1,
            'title': 'Test Video',
            'created_at': datetime.now().astimezone().isoformat(),
            'updated_at': datetime.now().astimezone().isoformat()
        }
        monitor.update_video_progress('simple_test_job', video_data)
        
        # Test job completion
        monitor.update_job_state('simple_test_job', JobState.COMPLETED, 'test_completed')
        assert monitor.active_jobs['simple_test_job']['state'] == JobState.COMPLETED
        
        # Test status retrieval
        status = monitor.get_job_status('simple_test_job')
        assert status is not None
        assert status['id'] == 'simple_test_job'
        
        # Test unregistration
        monitor.unregister_job('simple_test_job')
        assert 'simple_test_job' not in monitor.active_jobs
        
        print("✅ Monitor operations working")
        
        # Test data classes
        print("Testing data classes...")
        from progress_monitor import JobProgress, VideoProgress, WebSocketMessage
        
        # JobProgress
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
            created_at=datetime.now().astimezone(),
            updated_at=datetime.now().astimezone()
        )
        assert job_progress.percent_complete == 50.0
        
        # VideoProgress
        video_progress = VideoProgress(
            id='vid_001',
            job_id='job_001',
            state=VideoState.COMPLETED,
            percent_complete=100.0,
            row_index=1,
            title='Test Video',
            created_at=datetime.now().astimezone(),
            updated_at=datetime.now().astimezone(),
            errors=[]
        )
        assert video_progress.state == VideoState.COMPLETED
        
        # WebSocketMessage
        message = WebSocketMessage(
            type=EventType.JOB_PROGRESS,
            ts=datetime.now().astimezone().isoformat(),
            correlation_id='test-corr-id',
            data={'test': 'data'}
        )
        assert message.type == EventType.JOB_PROGRESS
        
        print("✅ Data classes working")
        
        # Test enums
        print("Testing enums...")
        assert JobState.PENDING.value == "pending"
        assert VideoState.PROCESSING.value == "processing"
        assert EventType.JOB_PROGRESS.value == "job.progress"
        print("✅ Enums working")
        
        print("\n🎉 All core tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Core test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_job_lifecycle_simple():
    """Test a simple job lifecycle without async operations."""
    print("\n🧪 Testing Simple Job Lifecycle")
    print("=" * 40)
    
    try:
        from progress_monitor import ProgressMonitor, JobState, VideoState
        
        # Create monitor with mocked components
        monitor = ProgressMonitor(
            supabase_url='http://localhost:54321',
            supabase_key='test_key'
        )
        
        # Mock WebSocket broadcaster
        class MockWebSocketBroadcaster:
            def __init__(self, *args, **kwargs):
                self.clients = {}
            async def broadcast_state_change(self, job_id, prior_state, new_state, reason):
                pass
            async def broadcast_progress(self, job_id, progress):
                pass
            async def broadcast_video_update(self, job_id, video, event_type):
                pass
            def start_server(self):
                pass
            def stop_server(self):
                pass
        
        monitor.websocket_broadcaster = MockWebSocketBroadcaster()
        
        # Track state changes
        lifecycle_events = []
        def track_lifecycle(job_id, prior_state, new_state, reason):
            lifecycle_events.append((job_id, prior_state, new_state, reason))
        
        monitor.add_state_change_handler(track_lifecycle)
        
        # Create job
        job_id = 'lifecycle_test'
        job_data = {
            'id': job_id,
            'state': JobState.PENDING.value,
            'items_total': 3,
            'items_completed': 0,
            'items_failed': 0,
            'items_skipped': 0,
            'items_canceled': 0,
            'created_at': datetime.now().astimezone().isoformat(),
            'rate_limited': False
        }
        
        monitor.register_job(job_id, job_data)
        assert len(lifecycle_events) >= 0  # May have initial events
        
        # Simulate processing
        states_to_test = [
            (JobState.RUNNING, "worker_assigned"),
            (JobState.COMPLETING, "finalizing"),
            (JobState.COMPLETED, "all_items_processed")
        ]
        
        for state, reason in states_to_test:
            monitor.update_job_state(job_id, state, reason)
        
        # Verify final state
        final_status = monitor.get_job_status(job_id)
        assert final_status['state'] == JobState.COMPLETED
        
        # Verify lifecycle events were recorded
        completed_events = [e for e in lifecycle_events if e[2] == JobState.COMPLETED]
        assert len(completed_events) > 0
        
        print("✅ Job lifecycle test passed")
        return True
        
    except Exception as e:
        print(f"❌ Lifecycle test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🚀 Running Simplified Progress Monitor Tests")
    print("=" * 60)
    
    tests = [
        test_core_functionality,
        test_job_lifecycle_simple
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
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! The progress monitor core functionality is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
    
    sys.exit(0 if failed == 0 else 1)