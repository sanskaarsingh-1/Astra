import pytest
from pathlib import Path
from fastapi import UploadFile
from gateway.validator import validate_upload_files

class MockUploadFile:
    def __init__(self, filename: str, content: bytes):
        self.filename = filename
        self._content = content
        self.size = len(content)

    async def read(self):
        return self._content
        
    async def seek(self, pos):
        pass

@pytest.mark.asyncio
async def test_validate_empty_files():
    errors = await validate_upload_files([])
    assert errors == ["No files provided."]

@pytest.mark.asyncio
async def test_validate_invalid_extension():
    # Valid mime format header for PNG, but wrong extension
    png_header = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR'
    files = [MockUploadFile("test.pdf", png_header)]
    errors = await validate_upload_files(files)
    assert errors is not None
    assert any("unsupported extension" in e for e in errors)
    
@pytest.mark.asyncio
async def test_validate_invalid_mime():
    # Valid extension, but invalid mime content (not an image)
    text_content = b'This is just a text file.'
    files = [MockUploadFile("test.png", text_content)]
    errors = await validate_upload_files(files)
    assert errors is not None
    assert any("unsupported MIME type" in e for e in errors)

@pytest.mark.asyncio
async def test_validate_valid_file():
    # Valid extension, valid mime format
    png_header = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR'
    files = [MockUploadFile("test.png", png_header)]
    errors = await validate_upload_files(files)
    assert errors is None
