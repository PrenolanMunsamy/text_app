import pytest
from app.app import app  # your Flask app
import io
import pandas as pd
from unittest.mock import patch
import os
from app.app import app, RESULTS_DIR

@pytest.fixture
def client(tmp_path):
    # Set RESULTS_DIR env before Flask app uses it
    os.environ["RESULTS_DIR"] = str(tmp_path)
    
    with app.test_client() as client:
        yield client

def test_home_page(client):
    """Test that the home page returns 200 and contains expected content."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"Text Analysis App" in response.data
    assert b"<form" in response.data

def test_upload_valid_csv(client):
    """Test uploading a valid CSV triggers the Celery task and returns success message."""
    # Create a simple CSV in memory as bytes
    csv_data = pd.DataFrame({"text": ["Hello world", "Test message"]})
    csv_bytes = io.BytesIO()
    csv_data.to_csv(csv_bytes, index=False, encoding='utf-8')
    csv_bytes.seek(0)  # rewind file to the beginning

    # Patch the Celery task so it doesn't actually run
    with patch("app.tasks.process_batch_and_email.apply_async") as mock_task:
        response = client.post(
            "/upload",
            data={
                "file": (csv_bytes, "test.csv"),
                "email": "test@example.com"
            },
            content_type="multipart/form-data"
        )

        # Check the response
        assert response.status_code == 200
        assert b"Upload successful" in response.data
        assert b"test@example.com" in response.data

        # Check that Celery task was called once
        mock_task.assert_called_once()

def test_upload_csv_missing_text_column(client):
    """Test uploading a CSV without a 'text' column returns a 400 error."""
    # Create a CSV without 'text' column
    csv_data = pd.DataFrame({"wrong_column": ["Hello world", "Test message"]})
    csv_bytes = io.BytesIO()
    csv_data.to_csv(csv_bytes, index=False, encoding='utf-8')
    csv_bytes.seek(0)

    # Patch the Celery task just in case
    with patch("app.tasks.process_batch_and_email.apply_async") as mock_task:
        response = client.post(
            "/upload",
            data={
                "file": (csv_bytes, "test.csv"),
                "email": "test@example.com"
            },
            content_type="multipart/form-data"
        )

        # The response should indicate the missing 'text' column
        assert response.status_code == 400
        assert b"CSV must have a 'text' column" in response.data

        # The Celery task should NOT have been called
        mock_task.assert_not_called()

def test_upload_no_file(client):
    """Test submitting the upload form without a file returns 400."""
    # Patch Celery just in case
    with patch("app.tasks.process_batch_and_email.apply_async") as mock_task:
        response = client.post(
            "/upload",
            data={
                "email": "test@example.com"  # no file included
            },
            content_type="multipart/form-data"
        )

        # Response should indicate no file uploaded
        assert response.status_code == 400
        assert b"No file uploaded" in response.data

        # Celery task should not have been called
        mock_task.assert_not_called()



def test_download_existing_file(tmp_path):
    """Test downloading an existing CSV file returns the file content."""
    batch_id = "123456"
    file_path = tmp_path / f"{batch_id}.csv"
    file_path.write_text("text,topic,sentiment\nHello,finance,positive\n")

    # Patch RESULTS_DIR in app directly
    from unittest.mock import patch
    with patch("app.app.RESULTS_DIR", tmp_path):
        with app.test_client() as client:
            response = client.get(f"/download/{batch_id}")

        assert response.status_code == 200
        assert b"Hello,finance,positive" in response.data

import pytest
from app.app import app
from unittest.mock import patch, MagicMock

def test_get_result_route():
    """Test /result/<task_id> route with pending and ready Celery tasks."""

    task_id = "fake-task-id"
    
    # --- Case 1: Task not ready ---
    mock_res_pending = MagicMock()
    mock_res_pending.ready.return_value = False
    
    with patch("app.app.AsyncResult", return_value=mock_res_pending):
        with app.test_client() as client:
            response = client.get(f"/result/{task_id}")
            assert response.status_code == 200
            assert response.json == {"status": "pending"}

    # --- Case 2: Task ready ---
    mock_res_ready = MagicMock()
    mock_res_ready.ready.return_value = True
    mock_res_ready.result = {"text": "Test", "topic": "tech", "sentiment": "positive"}
    
    with patch("app.app.AsyncResult", return_value=mock_res_ready):
        with app.test_client() as client:
            response = client.get(f"/result/{task_id}")
            assert response.status_code == 200
            assert response.json == {"text": "Test", "topic": "tech", "sentiment": "positive"}
