"""
Cancellable Processor Component
================================

Provides ability to cancel long-running AI processes.
Fixes the issue where users can't stop AI operations mid-way.
"""

import streamlit as st
import threading
import time
import uuid
import logging
from typing import Callable, Any, Optional, Dict
from dataclasses import dataclass
from datetime import datetime
import queue

logger = logging.getLogger(__name__)

@dataclass
class ProcessTask:
    """Represents a cancellable task"""
    id: str
    name: str
    func: Callable
    args: tuple
    kwargs: dict
    status: str = 'pending'  # pending, running, completed, cancelled, failed
    progress: float = 0.0
    result: Any = None
    error: Optional[Exception] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class CancellableProcessor:
    """Manages cancellable AI processes with progress tracking"""
    
    def __init__(self):
        self.tasks: Dict[str, ProcessTask] = {}
        self.active_threads: Dict[str, threading.Thread] = {}
        self.cancel_events: Dict[str, threading.Event] = {}
        self.progress_queues: Dict[str, queue.Queue] = {}
        
    def create_task(self, name: str, func: Callable, *args, **kwargs) -> str:
        """Create a new cancellable task"""
        task_id = str(uuid.uuid4())
        task = ProcessTask(
            id=task_id,
            name=name,
            func=func,
            args=args,
            kwargs=kwargs
        )
        self.tasks[task_id] = task
        self.cancel_events[task_id] = threading.Event()
        self.progress_queues[task_id] = queue.Queue()
        
        logger.info(f"Created task {task_id}: {name}")
        return task_id
    
    def run_with_cancel_button(self, name: str, func: Callable, *args, **kwargs) -> Any:
        """Run a process with cancel button in UI"""
        task_id = self.create_task(name, func, *args, **kwargs)
        
        # Create UI container
        container = st.container()
        
        with container:
            # Header with task name
            col1, col2 = st.columns([4, 1])
            
            with col1:
                st.markdown(f"### 🔄 {name}")
            
            with col2:
                cancel_button = st.button(
                    "🛑 Cancel",
                    key=f"cancel_{task_id}",
                    type="secondary",
                    help="Stop this process"
                )
            
            # Progress display
            progress_bar = st.progress(0.0)
            status_text = st.empty()
            time_text = st.empty()
            
            # Handle cancel
            if cancel_button:
                self.cancel_task(task_id)
                st.warning("⚠️ Cancellation requested...")
                return None
            
            # Start the task
            result_container = st.empty()
            
            def run_task():
                """Run the task in thread"""
                task = self.tasks[task_id]
                task.status = 'running'
                task.start_time = datetime.now()
                
                try:
                    # Wrap the function to check for cancellation
                    def wrapped_func(*args, **kwargs):
                        # Pass cancel event to function if it accepts it
                        if 'cancel_event' in func.__code__.co_varnames:
                            kwargs['cancel_event'] = self.cancel_events[task_id]
                        if 'progress_callback' in func.__code__.co_varnames:
                            kwargs['progress_callback'] = lambda p, msg="": self.update_progress(task_id, p, msg)
                        
                        return func(*args, **kwargs)
                    
                    result = wrapped_func(*task.args, **task.kwargs)
                    
                    if not self.cancel_events[task_id].is_set():
                        task.result = result
                        task.status = 'completed'
                    else:
                        task.status = 'cancelled'
                        
                except Exception as e:
                    task.error = e
                    task.status = 'failed'
                    logger.error(f"Task {task_id} failed: {e}")
                
                finally:
                    task.end_time = datetime.now()
                    self.progress_queues[task_id].put(('done', None))
            
            # Start thread
            thread = threading.Thread(target=run_task)
            self.active_threads[task_id] = thread
            thread.start()
            
            # Monitor progress
            while thread.is_alive() or not self.progress_queues[task_id].empty():
                try:
                    # Check for progress updates
                    update = self.progress_queues[task_id].get(timeout=0.1)
                    
                    if update[0] == 'progress':
                        progress, message = update[1]
                        progress_bar.progress(progress)
                        if message:
                            status_text.text(f"⚙️ {message}")
                        
                        # Update time
                        elapsed = (datetime.now() - self.tasks[task_id].start_time).total_seconds()
                        time_text.text(f"⏱️ {elapsed:.1f}s elapsed")
                        
                    elif update[0] == 'done':
                        break
                        
                except queue.Empty:
                    continue
                
                # Check if cancelled
                if self.cancel_events[task_id].is_set():
                    progress_bar.progress(1.0)
                    status_text.error("❌ Process cancelled")
                    return None
            
            # Show final result
            task = self.tasks[task_id]
            
            if task.status == 'completed':
                progress_bar.progress(1.0)
                elapsed = (task.end_time - task.start_time).total_seconds()
                status_text.success(f"✅ Completed in {elapsed:.1f}s")
                
                with result_container:
                    return task.result
                    
            elif task.status == 'cancelled':
                return None
                
            elif task.status == 'failed':
                st.error(f"❌ Process failed: {task.error}")
                return None
    
    def cancel_task(self, task_id: str):
        """Cancel a running task"""
        if task_id in self.cancel_events:
            self.cancel_events[task_id].set()
            logger.info(f"Cancelled task {task_id}")
            
            # Update task status
            if task_id in self.tasks:
                self.tasks[task_id].status = 'cancelled'
    
    def update_progress(self, task_id: str, progress: float, message: str = ""):
        """Update task progress"""
        if task_id in self.tasks:
            self.tasks[task_id].progress = progress
            self.progress_queues[task_id].put(('progress', (progress, message)))
    
    def cleanup_completed_tasks(self, older_than_seconds: int = 300):
        """Clean up old completed tasks"""
        now = datetime.now()
        tasks_to_remove = []
        
        for task_id, task in self.tasks.items():
            if task.status in ['completed', 'cancelled', 'failed']:
                if task.end_time and (now - task.end_time).total_seconds() > older_than_seconds:
                    tasks_to_remove.append(task_id)
        
        for task_id in tasks_to_remove:
            self._remove_task(task_id)
            
        logger.info(f"Cleaned up {len(tasks_to_remove)} old tasks")
    
    def _remove_task(self, task_id: str):
        """Remove a task and its resources"""
        self.tasks.pop(task_id, None)
        self.cancel_events.pop(task_id, None)
        self.progress_queues.pop(task_id, None)
        self.active_threads.pop(task_id, None)
    
    def get_active_tasks(self) -> list:
        """Get list of active tasks"""
        return [
            task for task in self.tasks.values()
            if task.status in ['pending', 'running']
        ]
    
    def cancel_all_tasks(self):
        """Cancel all active tasks"""
        for task_id in list(self.cancel_events.keys()):
            self.cancel_task(task_id)


# Singleton instance
_processor_instance = None

def get_cancellable_processor() -> CancellableProcessor:
    """Get singleton processor instance"""
    global _processor_instance
    if _processor_instance is None:
        _processor_instance = CancellableProcessor()
    return _processor_instance


# Example usage functions
def example_long_process(text: str, cancel_event: threading.Event = None, 
                        progress_callback: Callable = None) -> str:
    """Example of a cancellable process"""
    steps = 10
    
    for i in range(steps):
        # Check if cancelled
        if cancel_event and cancel_event.is_set():
            return None
        
        # Simulate work
        time.sleep(1)
        
        # Update progress
        if progress_callback:
            progress = (i + 1) / steps
            progress_callback(progress, f"Processing step {i+1}/{steps}")
    
    return f"Processed: {text}"


def make_cancellable(func: Callable) -> Callable:
    """Decorator to make a function cancellable"""
    def wrapper(*args, **kwargs):
        processor = get_cancellable_processor()
        return processor.run_with_cancel_button(
            func.__name__,
            func,
            *args,
            **kwargs
        )
    return wrapper


# UI Component for active tasks
def render_active_tasks():
    """Render list of active tasks with cancel buttons"""
    processor = get_cancellable_processor()
    active_tasks = processor.get_active_tasks()
    
    if active_tasks:
        st.markdown("### 🔄 Active Processes")
        
        for task in active_tasks:
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.text(f"📋 {task.name}")
            
            with col2:
                st.progress(task.progress)
            
            with col3:
                if st.button("Cancel", key=f"cancel_list_{task.id}"):
                    processor.cancel_task(task.id)
                    st.rerun()
        
        # Cancel all button
        if len(active_tasks) > 1:
            if st.button("🛑 Cancel All", type="secondary"):
                processor.cancel_all_tasks()
                st.rerun()
    else:
        st.info("No active processes")