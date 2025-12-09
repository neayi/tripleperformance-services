#!/usr/bin/env python
"""
Test script for transcription pipeline.
Tests each step independently.
"""
import sys
import os
sys.path.insert(0, '/app')

from app.database import SessionLocal, init_db
from app.transcription_service import TranscriptionService
from app import tasks as task_service

# Initialize database
init_db()

# Test video URL
VIDEO_URL = "https://www.youtube.com/watch?v=bpCdQ9RP9oc"
PAGE_NAME = "Test Page"
WIKI_LANG = "fr"

def test_create_task():
    """Test Step 1: Create transcription task"""
    print("=" * 60)
    print("TEST 1: Creating transcription task")
    print("=" * 60)

    service = TranscriptionService()
    db = SessionLocal()

    try:
        result = service.create_transcription_task(
            db,
            video_url=VIDEO_URL,
            page_name=PAGE_NAME,
            wiki_lang=WIKI_LANG
        )

        print(f"Success: {result['success']}")
        print(f"Message: {result['message']}")
        print(f"Task ID: {result.get('task_id')}")

        if result['success']:
            # Get task details
            task = task_service.get_task(db, result['task_id'])
            print(f"\nTask Details:")
            print(f"  ID: {task.id}")
            print(f"  Type: {task.task_type}")
            print(f"  Status: {task.status.value}")
            print(f"  Video URL: {task.video_url}")
            print(f"  Page Name: {task.page_name}")
            print(f"  Wiki Lang: {task.wiki_lang}")
            print(f"  Created: {task.created_at}")

            return task.id
        return None
    finally:
        db.close()

def test_list_tasks():
    """Test: List all tasks"""
    print("\n" + "=" * 60)
    print("TEST: Listing all tasks")
    print("=" * 60)

    db = SessionLocal()
    try:
        tasks = task_service.get_tasks(db)
        print(f"Total tasks: {len(tasks)}")
        for task in tasks:
            print(f"  - Task {task.id}: {task.task_type} | Status: {task.status.value} | Video: {task.video_url}")
    finally:
        db.close()

if __name__ == "__main__":
    # Test 1: Create task
    task_id = test_create_task()

    # Test 2: List tasks
    test_list_tasks()

    if task_id:
        print(f"\n✅ Task {task_id} created successfully!")
        print(f"\nNext steps:")
        print(f"1. Run the worker: docker exec tripleperformance-services python /app/workers/process_transcriptions.py")
        print(f"2. Check audio file: ls -lh /app/audio/")
        print(f"3. Access audio: curl http://localhost:8000/audio/<filename>")
    else:
        print("\n❌ Task creation failed!")
        sys.exit(1)
